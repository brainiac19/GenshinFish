import copy
import ctypes
import operator
import time
import winreg
from time import sleep

import cv2
import keyboard
import numpy as np
import pyautogui
import win32api
import win32con
from PIL import Image
from PIL import ImageEnhance
from win32gui import FindWindow, GetWindowRect

windowBarHeight = 32
windowMargin = 8
casting_path = 'templates/casting.png'
cancel_hook_path = 'templates/Cancel_hook.png'
pulling_path = 'templates/pulling.png'
test_pic_path = 'test.png'
progress_bar_path = 'templates/Progress_bar.png'
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
        self.screenWH = (win32api.GetSystemMetrics(0),win32api.GetSystemMetrics(1))
        self.gameWindowRect = self.get_game_windowRect()

        self.casting = cv2.imread(casting_path)
        self.pulling = cv2.imread(pulling_path)
        self.cancel_hook = cv2.imread(cancel_hook_path)
        self.progress_bar = cv2.imread(progress_bar_path)
        self.arrow_left = cv2.imread(arrow_left_path)
        self.arrow_right = cv2.imread(arrow_right_path)
        self.cursor = cv2.imread(cursor_path)

        self.casting,self.pulling,self.cancel_hook,self.progress_bar,self.arrow_left,self.arrow_right,self.cursor = \
        self.fit_template_size(self.casting,self.pulling,self.cancel_hook,self.progress_bar,self.arrow_left,self.arrow_right,self.cursor)

        self.cancel_hook_threshold = 0.8
        self.cancel_hook_changed_threshold = 0.5
        self.casting_threshold = 0.8
        self.pulling_threshold = 0.75
        self.progress_bar_area_width_to_progress_bar_width = 1.2
        self.progress_bar_area_height_to_progress_bar_height = 3


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

    def show_img(self, img, cvtColor = False):
        image = copy.deepcopy(img)
        if cvtColor:
            image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        cv2.namedWindow('111')  # Create a named window
        cv2.moveWindow('111', 0, 0)
        cv2.imshow('111',image)
        cv2.waitKey(2000)
        cv2.destroyAllWindows()

    def anchor_to_center(self,img,anchor_coords):
        return (int(img.shape[1] / 2 + anchor_coords[0]), int(img.shape[0] / 2 + anchor_coords[1]))

    def get_game_windowRect(self):
        gameWindowRes = self.get_game_resolution()
        if operator.eq(gameWindowRes, self.screenWH):
            return (0,0,*gameWindowRes)
        gameWindowRect = self.locate_game_window()
        return (*gameWindowRect[:2],*gameWindowRes)

    def get_game_screen(self):
        fullscreen = Utils.PIL2CV(Utils.captureScreen())
        self.gameWindowRect = self.get_game_windowRect()
        gameScreen = fullscreen[self.gameWindowRect[1]+windowBarHeight:self.gameWindowRect[1]+self.gameWindowRect[3]+windowBarHeight,self.gameWindowRect[0]+windowMargin:self.gameWindowRect[0]+self.gameWindowRect[2]+windowMargin]
        return gameScreen

    def fit_template_size(self, *templates):
        if self.gameWindowRect[2]/self.gameWindowRect[3] - self.screenWH[0]/self.screenWH[1]>0.001:
            factor = self.gameWindowRect[3]/self.screenWH[1]
        elif self.gameWindowRect[2]/self.gameWindowRect[3] - self.screenWH[0]/self.screenWH[1]<-0.001:
            factor = self.gameWindowRect[2] / self.screenWH[0]
        else:
            factor = self.gameWindowRect[3] / self.screenWH[1]

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

    def locate_template(self, img, template, mask=None, fitnum = 0.95):
        res = cv2.matchTemplate(img, template, cv2.TM_CCORR_NORMED,None,mask)
        best_fit = max(np.reshape(res,(-1,1)))
        if best_fit < fitnum:
            return None
        best_position = tuple(zip(*np.where(res == best_fit)))[0]
        return (best_position[1],best_position[0]),best_fit[0]

class Clicker:
    def __init__(self):

        self.check_done_fishing_count = 5
        self.main()


    def main(self):
        print('started')
        while(True):
            self.image_ops = ImageOperations()
            #wait for casting rod, locate hook icon
            while(True):
                if keyboard.is_pressed('p'):
                    print('stopped')
                    return
                waiting_screen = self.image_ops.get_game_screen()
                cropped, start, end = self.image_ops.crop_img_by_percentage(waiting_screen, -1 / 4, -1 / 5)
                adjusted = self.image_ops.img_to_bw(self.image_ops.adjust_contrast(3, cropped), 200)

                result = self.image_ops.locate_template(adjusted,
                                                        cv2.cvtColor(self.image_ops.cancel_hook, cv2.COLOR_BGR2GRAY), None,
                                                        0.8)
                if result is None or result[1] < self.image_ops.cancel_hook_threshold:
                    time.sleep(0.2)
                    continue
                else:
                    coords_to_game_screen = self.image_ops.bigger_area_coords(start, result[0])
                    core_icon_rect = self.image_ops.expand_rect((*coords_to_game_screen,*self.image_ops.cancel_hook.shape[:2][::-1]),50,50)
                    print("rod casted!")
                    break

            #wait til hooked, or cancelled
            while(True):
                if keyboard.is_pressed('p'):
                    print('stopped')
                    return
                new_screen = self.image_ops.get_game_screen()
                cropped = new_screen[coords_to_game_screen[1]:coords_to_game_screen[1] + self.image_ops.cancel_hook.shape[0], coords_to_game_screen[0]:coords_to_game_screen[0] + self.image_ops.cancel_hook.shape[1]]
                adjusted = self.image_ops.img_to_bw(self.image_ops.adjust_contrast(3, cropped), 200)
                changed = self.image_ops.locate_template(adjusted, cv2.cvtColor(self.image_ops.cancel_hook, cv2.COLOR_BGR2GRAY), None, 0)[1] < self.image_ops.cancel_hook_changed_threshold
                if changed:
                    break

            cropped = new_screen[core_icon_rect[1]:core_icon_rect[1] + core_icon_rect[3], core_icon_rect[0]:core_icon_rect[0] + core_icon_rect[2]]
            adjusted = self.image_ops.img_to_bw(self.image_ops.adjust_contrast(3, cropped), 200)
            exited = self.image_ops.locate_template(adjusted, cv2.cvtColor(self.image_ops.casting, cv2.COLOR_BGR2GRAY), None, 0)[1] > self.image_ops.casting_threshold
            if exited:
                print('exited.')
                continue
            else:
                print('hooked!')

            self.mouse_down()
            sleep(0.7)
            self.mouse_up()

            #find progress bar
            new_screen = self.image_ops.get_game_screen()
            crop_1st,start,end = self.image_ops.crop_img_by_percentage(new_screen,-7 / 10, 1 / 4)
            crop_2nd = self.image_ops.crop_img_by_percentage(crop_1st,4 / 7, 1)[0]
            bar = self.image_ops.locate_template(crop_2nd, self.image_ops.progress_bar, self.image_ops.progress_bar, 0.8)[0]
            progress_bar_center_to_game = self.image_ops.bigger_area_coords(start,self.image_ops.anchor_to_center(self.image_ops.progress_bar,bar))
            progress_bar_area_rect = (int(progress_bar_center_to_game[0] - self.image_ops.progress_bar.shape[1] / 2 * self.image_ops.progress_bar_area_width_to_progress_bar_width),
                                      int(progress_bar_center_to_game[1] - self.image_ops.progress_bar.shape[0] / 2 * self.image_ops.progress_bar_area_height_to_progress_bar_height),
                                      int(self.image_ops.progress_bar.shape[1] * self.image_ops.progress_bar_area_width_to_progress_bar_width),
                                      int(self.image_ops.progress_bar.shape[0] * self.image_ops.progress_bar_area_height_to_progress_bar_height))

            #self.image_ops.ShowImg(new_screen[progress_bar_area_rect[1]:progress_bar_area_rect[1] + progress_bar_area_rect[3], progress_bar_area_rect[0]:progress_bar_area_rect[0] + progress_bar_area_rect[2]])
            #cursor = self.image_ops.locate_template(crop_2nd,self.image_ops.cursor,self.image_ops.cursor,0.8)
            #cursor_pos_to_game = self.image_ops.bigger_area_coords(start,cursor[0])
            #cursor_center = self.image_ops.anchor_to_center(self.image_ops.cursor,cursor_pos_to_game)
            #progress_bar_WH = (int(self.image_ops.cursor.shape[0] * self.image_ops.progress_bar_rect_length_to_cursor_height), int(self.image_ops.cursor.shape[1]* self.image_ops.progress_bar_rect_height_to_cursor_height))
            #progress_bar_rect = (int(cursor_center[0] - progress_bar_WH[0] / 2), int(cursor_center[1] - progress_bar_WH[1]/2),*progress_bar_WH)
            #print(progress_bar_rect)
            cycle_count = 0

            print("controlling...")
            while(True):
                cycle_count +=1
                #t1 = time.time()
                new_screen = self.image_ops.get_game_screen()
                cropped = new_screen[progress_bar_area_rect[1]:progress_bar_area_rect[1] + progress_bar_area_rect[3], progress_bar_area_rect[0]:progress_bar_area_rect[0] + progress_bar_area_rect[2]]
                # match_area_by_color = self.image_ops.coords_of_close_colors(cropped)
                #
                #
                # if len(match_area_by_color) == 0:
                #     print('done fishing!')
                #     break
                #
                # zipped = list(zip(*match_area_by_color))
                # left_limit = min(zipped[0])
                # right_limit = max(zipped[0])

                #check if done fishing
                if cycle_count % self.check_done_fishing_count == 0:
                    done_cropped = new_screen[core_icon_rect[1]:core_icon_rect[1] + core_icon_rect[3], core_icon_rect[0]:core_icon_rect[0] + core_icon_rect[2]]
                    adjusted = self.image_ops.img_to_bw(self.image_ops.adjust_contrast(3, done_cropped), 200)
                    finished = self.image_ops.locate_template(adjusted,cv2.cvtColor(self.image_ops.pulling, cv2.COLOR_BGR2GRAY),None,0)[1] < self.image_ops.pulling_threshold
                    if finished:
                        print('done fishing!')
                        break


                arrow_l = self.image_ops.locate_template(cropped,self.image_ops.arrow_left,None,0)
                arrow_r = self.image_ops.locate_template(cropped, self.image_ops.arrow_right, None,
                                                         0)
                cursor = self.image_ops.locate_template(cropped, self.image_ops.cursor, None,
                                                         0)

                #rough check on whether done fishing
                if keyboard.is_pressed('k') or arrow_l is None or arrow_r is None and cursor is None:
                    print('done fishing!')
                    break




                #center_between_arrows_x = (left_limit + right_limit) / 2
                center_between_arrows_x = (arrow_l[0][0] + arrow_r[0][0]) / 2

                if cursor[0][0] < center_between_arrows_x:
                    self.click()

                # if cursor[0][0] < center_between_arrows_x:
                #     if not self.mouse_status:
                #         self.mouse_down()
                # elif cursor[0][0] > center_between_arrows_x:
                #     if self.mouse_status:
                #         self.mouse_up()

                # t2 = time.time()
                # print(t2-t1)


    def mouse_down(self):
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, *win32api.GetCursorPos(), 0, 0)
        self.mouse_status = True

    def mouse_up(self):
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, *win32api.GetCursorPos(), 0, 0)
        self.mouse_status = False

    def click(self,x=None, y=None):
        if x is not None and y is not None:
            x = int(x)
            y = int(y)
            ctypes.windll.user32.SetCursorPos(x, y)
            time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, *win32api.GetCursorPos(), 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, *win32api.GetCursorPos(), 0, 0)

    def move(self,x,y):
        x=int(x)
        y=int(y)
        ctypes.windll.user32.SetCursorPos(x, y)


Clicker()
