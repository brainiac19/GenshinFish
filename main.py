import copy
import ctypes
import operator
import time
import winreg
from time import sleep
import mss
import cv2
import keyboard
import numpy as np
import pyautogui
import win32api
import win32con
from PIL import Image
from PIL import ImageEnhance
from win32gui import FindWindow, GetWindowRect

windowBarHeight = 33
windowMargin = 2
casting_path = 'templates/casting.png'
hook_path = 'templates/hook.png'
pulling_path = 'templates/pulling.png'
progress_bar_path = 'templates/progress_bar.png'
arrow_left_path = 'templates/Arrow_L.png'
arrow_right_path = 'templates/Arrow_R.png'
cursor_path = 'templates/Cursor.png'
gameWindowName = 'Genshin Impact'

class Utils:
    @staticmethod
    def captureScreen():
        return pyautogui.screenshot()

    @staticmethod
    def PIL2CV(img):
        img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        return img

    @staticmethod
    def CV2PIL(img):
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        return img


class ImageOperations:
    def __init__(self):
        self.mss_instance = mss.mss()
        self.screenWH = (win32api.GetSystemMetrics(0),win32api.GetSystemMetrics(1))
        self.template_standard_size = (1920,1080)
        self.gameWindowRect = self.get_game_windowRect()
        #self.gameWindowRect = (0,0,1920,1080)
        self.dark_yellow = np.array((160,225,225), dtype=np.uint8)
        self.bright_yellow = np.array((210,255,255), dtype=np.uint8)
        self.bright_green_low = np.array((190, 240, 60), dtype=np.uint8)
        self.bright_green_high = np.array((215, 255, 85), dtype=np.uint8)
        self.dark_green_low = np.array((75, 100, 35), dtype=np.uint8)
        self.dark_green_high = np.array((105, 130, 60), dtype=np.uint8)
        self.dark_orange_low = np.array((50, 200, 240), dtype=np.uint8)
        self.dark_orange_high = np.array((70, 230, 255), dtype=np.uint8)


        self.casting = cv2.cvtColor(cv2.imread(casting_path),cv2.COLOR_BGR2GRAY)
        self.pulling = cv2.cvtColor(cv2.imread(pulling_path),cv2.COLOR_BGR2GRAY)
        self.hook = cv2.cvtColor(cv2.imread(hook_path),cv2.COLOR_BGR2GRAY)
        self.progress_bar = cv2.imread(progress_bar_path)
        self.arrow_left = cv2.cvtColor(cv2.imread(arrow_left_path),cv2.COLOR_BGR2GRAY)
        self.arrow_right = cv2.cvtColor(cv2.imread(arrow_right_path),cv2.COLOR_BGR2GRAY)
        self.cursor = cv2.cvtColor(cv2.imread(cursor_path),cv2.COLOR_BGR2GRAY)

        self.casting,self.pulling,self.hook,self.progress_bar,self.arrow_left,self.arrow_right,self.cursor = \
        self.fit_template_size(self.casting,self.pulling,self.hook,self.progress_bar,self.arrow_left,self.arrow_right,self.cursor)

        self.hook_threshold = 0.8
        self.hook_changed_threshold = 0.5
        self.casting_threshold = 0.8
        self.pulling_threshold = 0.75


    def get_progress_elements(self,img):
        bw_image = cv2.inRange(img, self.dark_yellow, self.bright_yellow)
        return bw_image

    def expand_rect(self,rect,x,y):
        return (int(rect[0] - x / 2), int(rect[1] - y / 2), int(rect[2] + x), int(rect[3] + y))

    def img_to_bw(self,img,thresh):
        grayImage = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        (thresh, blackAndWhiteImage) = cv2.threshold(grayImage, thresh, 255, cv2.THRESH_BINARY)
        return blackAndWhiteImage

    def adjust_contrast(self, contrast, image):
        enh_con = ImageEnhance.Contrast(Utils.CV2PIL(image))
        adjusted = Utils.PIL2CV(enh_con.enhance(contrast))
        return adjusted

    def is_full_screen(self):
        return operator.eq(self.gameWindowRect[2:4],self.screenWH)

    def show_img(self, img, time, cvtColor = False):
        image = copy.deepcopy(img)
        if cvtColor:
            image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        cv2.namedWindow('preview')  # Create a named window
        cv2.moveWindow('preview', 0, 0)
        cv2.imshow('preview',image)
        cv2.waitKey(time * 1000)
        cv2.destroyAllWindows()

    def anchor_to_center(self,img,anchor_coords):
        return (int(img.shape[1] / 2 + anchor_coords[0]), int(img.shape[0] / 2 + anchor_coords[1]))

    def get_game_windowRect(self):
        '''
        Game window rect as left, top, width, height
        From the upper left corner of the title bar, to the lower right corner of the game window
        :return:
        '''
        gameWindowRes = self.get_game_resolution()
        if operator.eq(gameWindowRes, self.screenWH):
            return (0,0,*gameWindowRes)
        gameWindowRect = self.locate_game_window()
        #return (*gameWindowRect[:2], *gameWindowRes)
        return (gameWindowRect[0] + windowMargin, gameWindowRect[1], gameWindowRes[0], gameWindowRes[1] + windowBarHeight) #problematic

    def get_game_screen(self):
        capture_rect = {"top": self.gameWindowRect[1]+windowBarHeight, "left": self.gameWindowRect[0],
                        "width": self.gameWindowRect[2],
                        "height": self.gameWindowRect[3]-windowBarHeight}
        screenshot = self.mss_instance.grab(capture_rect)
        gameScreen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGRA2BGR)
        return gameScreen

    def fit_template_size(self, *templates):
        if self.gameWindowRect[2]/self.gameWindowRect[3] - self.template_standard_size[0]/self.template_standard_size[1]>0.001:
            factor = self.gameWindowRect[3]/self.template_standard_size[1]
        elif self.gameWindowRect[2]/self.gameWindowRect[3] - self.template_standard_size[0]/self.template_standard_size[1]<-0.001:
            factor = self.gameWindowRect[2] / self.template_standard_size[0]
        else:
            factor = self.gameWindowRect[3] / self.template_standard_size[1]

        self.scaleFactor = factor

        cache = []

        for template in templates:
            cache.append(cv2.resize(template, tuple(round(shape * factor) for shape in template.shape[:2])[::-1],
                                     interpolation=cv2.INTER_AREA))

        return cache

    def get_game_resolution(self):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\miHoYo\Genshin Impact")
        gameWH = {}
        for i in range(winreg.QueryInfoKey(key)[1]):
            if len(gameWH.keys()) == 2:
                break
            value_name, value, datatype = winreg.EnumValue(key, i)
            if 'Width' in value_name:
                gameWH['width'] = value
            if 'Height' in value_name:
                gameWH['height'] = value

        return (gameWH['width'],gameWH['height'])

    def locate_game_window(self):
        window_handle = FindWindow(None, gameWindowName)
        window_rect = GetWindowRect(window_handle)
        if any(value < 0 for value in window_rect):
            raise Exception('failed to find game window!')
        return window_rect

    def game_coords_to_screen_coords(self, gameCoords):
        if self.is_full_screen():
            return gameCoords
        else:
            return (self.gameWindowRect[0]+gameCoords[0]+windowMargin,self.gameWindowRect[1]+gameCoords[1]+windowBarHeight)

    def bigger_area_coords(self,smaller_area_anchor_to_bigger_area,smaller_area_coords):
        return (smaller_area_anchor_to_bigger_area[0] + smaller_area_coords[0], smaller_area_anchor_to_bigger_area[1] + smaller_area_coords[1])

    def find_best_threshold(self, res, goalNum):
        currentFitnum = 0.9
        currentPrecision = 0.01
        currentMatchCount=len(np.where(res>currentFitnum)[0])

        while(not currentMatchCount == goalNum):
            if currentMatchCount > goalNum:
                currentFitnum += currentPrecision
            elif currentFitnum < goalNum:
                currentFitnum -= currentPrecision
                currentPrecision *= 0.1
                currentFitnum += currentPrecision
            else:
                break

            currentMatchCount = len(np.where(res>currentFitnum)[0])

        print(currentFitnum)
        return currentFitnum

    def crop_img_by_percentage(self,img,percentageW = 1.0,percentageH = 1.0):
        shape = img.shape
        if percentageW > 0:
            if percentageH > 0:
                start = (0,0)
                end = (int(shape[1] * percentageW),int(shape[0] * percentageH))
            if percentageH < 0:
                start = (0,int(shape[0] * (1 + percentageH)))
                end = (int(shape[1] * percentageW), shape[0])
        elif percentageW < 0:
            if percentageH > 0:
                start = (int(shape[1] * (1 + percentageW)),0)
                end = (shape[1], int(shape[0] * percentageH))
            if percentageH < 0:
                start = (int(shape[1] * (1 + percentageW)), int(shape[0] * (1 + percentageH)))
                end = (shape[1], shape[0])
        else:
            raise Exception("Wrong percentage!")

        return img[start[1]:end[1],start[0]:end[0]],start,end

    def coords_of_close_colors(self,img):
        result = []
        for i in range(img.shape[0]):
            for j in range(img.shape[1]):
                if img[i][j][2] == 255 and img[i][j][1] == 255 and 160 < img[i][j][0] < 200:
                    result.append((j,i))
        return result

    def locate_template(self, img, template, mask=None):
        res = cv2.matchTemplate(img, template, cv2.TM_CCORR_NORMED,None,mask)
        best_fit = max(np.reshape(res,(-1,1)))
        best_position = tuple(zip(*np.where(res == best_fit)))[0]
        return (best_position[1],best_position[0]),best_fit[0]

class Clicker:
    def __init__(self):

        self.capture_screen_wait_time = 0 #adjust this if screen recognition is affecting performance badly. KEEP IT BELOW 0.2
        self.main()

    def test(self):
        #experimental way of locating progress bar.

        #self.image_ops = ImageOperations()
        #now_screen = Utils.PIL2CV(Utils.captureScreen())
        # #get light green
        # light_green_bw = cv2.inRange(self.image_ops.error, self.image_ops.bright_green_low, self.image_ops.bright_green_high)
        # #get dark green
        # dark_green_bw = cv2.inRange(self.image_ops.error, self.image_ops.dark_green_low, self.image_ops.dark_green_high)
        # #combine

        #bw_image = self.image_ops.get_progress_elements(self.image_ops.test1)
        pass


    def main(self):
        print('Ready!')
        while(True):

            #wait for game window, then wait for casting rod, locate hook icon
            while(True):
                try:
                    self.image_ops = ImageOperations()
                except:
                    sleep(0.5)
                    continue
                new_screen = self.image_ops.get_game_screen()
                cropped_lower_right, start, end = self.image_ops.crop_img_by_percentage(new_screen, -1 / 4, -1 / 5)
                adjusted_lower_right = self.image_ops.img_to_bw(self.image_ops.adjust_contrast(3, cropped_lower_right), 200)

                result = self.image_ops.locate_template(adjusted_lower_right,self.image_ops.hook)
                if result is None or result[1] < self.image_ops.hook_threshold:
                    sleep(0.5)
                    continue
                else:
                    coords_to_game_screen = self.image_ops.bigger_area_coords(start, result[0])
                    core_icon_rect = self.image_ops.expand_rect((*coords_to_game_screen,*self.image_ops.hook.shape[:2][::-1]),50,50)
                    print("Rod casted!")
                    break

            #wait til hooked, or cancelled
            while(True):
                if keyboard.is_pressed('k'):
                    print('Interrupted!')
                    break
                new_screen = self.image_ops.get_game_screen()
                cropped_core_icon_area = new_screen[coords_to_game_screen[1]:coords_to_game_screen[1] + self.image_ops.hook.shape[0], coords_to_game_screen[0]:coords_to_game_screen[0] + self.image_ops.hook.shape[1]]
                adjusted_core_icon_area = self.image_ops.img_to_bw(self.image_ops.adjust_contrast(3, cropped_core_icon_area), 200)
                changed = self.image_ops.locate_template(adjusted_core_icon_area, self.image_ops.hook)[1] < self.image_ops.hook_changed_threshold
                if changed:
                    break

            #both cancelling fishing and hooking a fish could trigger change of hook icon
            cropped_core_icon_area = new_screen[core_icon_rect[1]:core_icon_rect[1] + core_icon_rect[3], core_icon_rect[0]:core_icon_rect[0] + core_icon_rect[2]]
            adjusted_core_icon_area = self.image_ops.img_to_bw(self.image_ops.adjust_contrast(3, cropped_core_icon_area), 200)
            cancelled = self.image_ops.locate_template(adjusted_core_icon_area, self.image_ops.casting)[1] > self.image_ops.casting_threshold
            if cancelled:
                print('Cancelled')
                continue
            else:
                print('Hooked!')

            self.mouse_down()
            #give the UI some time to pop up
            sleep(0.7)
            self.mouse_up()

            #find progress bar
            new_screen = self.image_ops.get_game_screen()

            #crop upper center part of the game screen
            dim = new_screen.shape[:2][::-1]
            crop_rect = (int(dim[0] * 3 / 10), 0, int(dim[0] * 4 / 10), int(dim[0] / 4))
            upper_center_area = new_screen[crop_rect[1]:crop_rect[1] + crop_rect[3], crop_rect[0]:crop_rect[0] + crop_rect[2]]

            located_progress_bar = self.image_ops.locate_template(upper_center_area, self.image_ops.progress_bar)
            progress_bar_pos_to_game = self.image_ops.bigger_area_coords(crop_rect[:2],located_progress_bar[0])
            progress_bar_area_rect = (*progress_bar_pos_to_game,*self.image_ops.progress_bar.shape[:2][::-1])



            print("Controlling...")
            while(True):
                if keyboard.is_pressed('k'):
                    print('Interrupted!')
                    break

                new_screen = self.image_ops.get_game_screen()
                #crop for progress bar area
                progress_bar_area = new_screen[progress_bar_area_rect[1]:progress_bar_area_rect[1] + progress_bar_area_rect[3], progress_bar_area_rect[0]:progress_bar_area_rect[0] + progress_bar_area_rect[2]]
                adjusted_progress_bar_area = self.image_ops.get_progress_elements(progress_bar_area)


                #try to locate arrow and cursor
                try:

                    arrow_l = self.image_ops.locate_template(adjusted_progress_bar_area, self.image_ops.arrow_left)
                    arrow_r = self.image_ops.locate_template(adjusted_progress_bar_area, self.image_ops.arrow_right)
                    cursor = self.image_ops.locate_template(adjusted_progress_bar_area, self.image_ops.cursor)


                    if arrow_l[1] < 0.5 or arrow_l[1] < 0.5 or  cursor[1] < 0.5:
                        raise Exception("Couldn't locate arrows")

                    center_between_arrows_x = (arrow_l[0][0] + arrow_r[0][0]) / 2
                    if cursor[0][0] < center_between_arrows_x:
                        self.click()
                    else:
                        sleep(self.capture_screen_wait_time)

                except:

                    done_cropped = new_screen[core_icon_rect[1]:core_icon_rect[1] + core_icon_rect[3], core_icon_rect[0]:core_icon_rect[0] + core_icon_rect[2]]
                    adjusted_done = self.image_ops.img_to_bw(self.image_ops.adjust_contrast(3, done_cropped), 200)
                    finished = self.image_ops.locate_template(adjusted_done, self.image_ops.pulling)[1] < self.image_ops.pulling_threshold
                    if finished:
                        print('Done fishing!')
                        break
                    else:
                        print("Lost track of progress, retrying!")
                        continue



    def click(self,x=None, y=None):
        if x is not None and y is not None:
            x = int(x)
            y = int(y)
            ctypes.windll.user32.SetCursorPos(x, y)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, *win32api.GetCursorPos(), 0, 0)
        sleep(self.capture_screen_wait_time)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, *win32api.GetCursorPos(), 0, 0)

    def mouse_down(self):
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, *win32api.GetCursorPos(), 0, 0)

    def mouse_up(self):
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, *win32api.GetCursorPos(), 0, 0)


Clicker()
