import copy
import operator
import winreg
from time import sleep, time
import os
import json
import mss
import cv2
import keyboard
import numpy as np
import win32api
import win32con
from PIL import Image
from PIL import ImageEnhance
from win32gui import FindWindow, GetWindowRect

class Utils:

    @staticmethod
    def PIL2CV(img):
        img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        return img

    @staticmethod
    def CV2PIL(img):
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        return img

class ImageOperations:
    def __init__(self,config):
        self.config = config
        self.mss_instance = mss.mss()
        self.screenWH = (win32api.GetSystemMetrics(0),win32api.GetSystemMetrics(1))
        self.game_window_res = self.get_game_resolution()
        self.templates_source_res = self.config['templates_source_resolution']
        self.game_window_rect = self.get_game_window_rect()
        self.lower_target_resolution = self.get_lower_target_resolution()

        self.cast_template = cv2.cvtColor(cv2.imread(self.config['templates_path']['cast_path']), cv2.COLOR_BGR2GRAY)
        self.pull_template = cv2.cvtColor(cv2.imread(self.config['templates_path']['pull_path']), cv2.COLOR_BGR2GRAY)
        self.hook_template = cv2.cvtColor(cv2.imread(self.config['templates_path']['hook_path']), cv2.COLOR_BGR2GRAY)
        self.progress_bar_template = cv2.imread(self.config['templates_path']['progress_bar_path'])
        self.arrow_left_template = cv2.cvtColor(cv2.imread(self.config['templates_path']['arrow_left_path']), cv2.COLOR_BGR2GRAY)
        self.arrow_right_template = cv2.cvtColor(cv2.imread(self.config['templates_path']['arrow_right_path']), cv2.COLOR_BGR2GRAY)
        self.cursor_template = cv2.cvtColor(cv2.imread(self.config['templates_path']['cursor_path']), cv2.COLOR_BGR2GRAY)

        self.cast_template_resized_to_game, self.pull_template_resized_to_game, self.hook_template_resized_to_game, self.progress_bar_template_resized_to_game, self.arrow_left_template_resized_to_game,\
        self.arrow_right_template_resized_to_game, self.cursor_template_resized_to_game = \
        self.fit_template_size(self.game_window_res, self.cast_template, self.pull_template, self.hook_template, self.progress_bar_template,
                               self.arrow_left_template, self.arrow_right_template, self.cursor_template)

        self.cast_template_resized_to_lower, self.pull_template_resized_to_lower, self.hook_template_resized_to_lower, self.progress_bar_template_resized_to_lower, self.arrow_left_template_resized_to_lower, \
        self.arrow_right_template_resized_to_lower, self.cursor_template_resized_to_lower = \
            self.fit_template_size(self.lower_target_resolution, self.cast_template, self.pull_template, self.hook_template,
                                   self.progress_bar_template,
                                   self.arrow_left_template, self.arrow_right_template, self.cursor_template)

        self.check_game_res()

    def get_lower_target_resolution(self):
        return tuple(map(lambda x,y:round((x-y)*(1 - self.config['lower_resolution_ratio']) + y),
                         self.game_window_res, self.config['lowest_resolution_allowed']))

    def check_game_res(self):
        if self.game_window_res[0] < self.config['lowest_resolution_allowed'][0] or \
            self.game_window_res[1] < self.config['lowest_resolution_allowed'][1]:
            print('Warning: Game resolution lower than allowed!')

    def get_progress_indicator_bw(self, img):
        bw_image = cv2.inRange(img, *np.array(self.config['color_threshold']['progress_indicator_bright_yellow'], dtype=np.uint8))
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
        return operator.eq(self.game_window_rect[2:4], self.screenWH)

    def show_img(self, img, time, cvtColor = False):
        image = copy.deepcopy(img)
        if cvtColor:
            image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        cv2.namedWindow('preview')  # Create a named window
        cv2.moveWindow('preview', 0, 0)
        cv2.imshow('preview',image)
        cv2.waitKey(int(time * 1000))
        cv2.destroyAllWindows()

    def anchor_to_center(self,img,anchor_coords):
        return (int(img.shape[1] / 2 + anchor_coords[0]), int(img.shape[0] / 2 + anchor_coords[1]))

    def get_game_window_rect(self):
        '''
        Game window rect as left, top, width, height
        From the upper left corner of the title bar, to the lower right corner of the game window
        :return:
        '''

        if operator.eq(self.game_window_res, self.screenWH):
            return (0,0,*self.game_window_res)
        else:
            gameWindowRect = self.locate_game_window()
            return (gameWindowRect[0] + self.config['window_margin'] * 2, gameWindowRect[1],
                    self.game_window_res[0],
                    self.game_window_res[1] + self.config['window_margin'] + self.config['window_caption_height'])

    def get_game_screen(self,rect= None):
        if rect is None:
            if operator.eq(self.game_window_res, self.screenWH):
                capture_rect = {
                    "top": self.game_window_rect[1],
                    "left": self.game_window_rect[0],
                    "width": self.game_window_rect[2],
                    "height": self.game_window_rect[3]}
            else:
                capture_rect = {"top": self.game_window_rect[1] + self.config['window_margin'] + self.config['window_caption_height'], "left": self.game_window_rect[0],
                                "width": self.game_window_rect[2],
                                "height": self.game_window_rect[3] - (self.config['window_margin'] + self.config['window_caption_height'])}
        else:
            if operator.eq(self.game_window_res, self.screenWH):
                capture_rect = {
                    "top": self.game_window_rect[1] + rect[1],
                    "left": self.game_window_rect[0] + rect[0],
                    "width": rect[2],
                    "height": rect[3]}
            else:
                capture_rect = {"top": self.game_window_rect[1] + self.config['window_margin'] + self.config['window_caption_height'] + rect[1],
                                "left": self.game_window_rect[0] + rect[0],
                                "width": rect[2],
                                "height": rect[3]}
        screenshot = self.mss_instance.grab(capture_rect)
        gameScreen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGRA2BGR)
        return gameScreen

    def get_low_res_game_screen(self, rect=None):
        return self.scale_image_preserve_ratio(self.get_game_screen(rect),
                                               self.game_window_res,
                                               self.lower_target_resolution)

    def get_scale_factor_preserve_ratio(self, src_resolution, dst_resolution):
        factor_xy = (dst_resolution[0] / src_resolution[0], dst_resolution[1] / src_resolution[1])
        return min(factor_xy)

    def scale_image_preserve_ratio(self, img, src_resolution, dst_resolution):
        scale_factor = self.get_scale_factor_preserve_ratio(src_resolution,dst_resolution)
        return cv2.resize(img,tuple(round(scale_factor * axis) for axis in img.shape[:2][::-1]),interpolation=cv2.INTER_AREA)

    def fit_template_size(self, target_resolution, *templates):
        cache = []
        for template in templates:
            cache.append(self.scale_image_preserve_ratio(template, self.templates_source_res, target_resolution))
        return cache

    def get_game_resolution(self):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.config['registry_path'])
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

    def get_game_window_title(self):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.config['registry_path'])
        for i in range(winreg.QueryInfoKey(key)[1]):
            value_name, value, datatype = winreg.EnumValue(key, i)
            if 'CURRENT_LANGUAGE' in value_name:
                language = value.decode('utf-8').rstrip('\x00')
                break
        try:
            window_title = self.config['title_in_languages'][language]
            return window_title
        except:
            raise KeyError("Language not found!")


    def locate_game_window(self):
        window_handle = FindWindow(None, self.get_game_window_title())
        window_rect = GetWindowRect(window_handle)
        if any(value < 0 for value in window_rect):
            raise Exception('failed to find game window!')
        return window_rect

    def game_coords_to_screen_coords(self, gameCoords):
        if operator.eq(self.game_window_res, self.screenWH):
            return gameCoords
        else:
            return (self.game_window_rect[0] + gameCoords[0] + self.config['window_margin'], self.game_window_rect[1] + gameCoords[1] + self.config['window_margin'] + self.config['window_caption_height'])

    def parent_area_coords(self, child_area_anchor_to_parent_area, child_area_coords):
        return (child_area_anchor_to_parent_area[0] + child_area_coords[0], child_area_anchor_to_parent_area[1] + child_area_coords[1])

    def low_res_to_high_res_coords(self,low_res_coords, low_res_shape, high_res_shape):
        factor = self.get_scale_factor_preserve_ratio(self.game_window_res,self.lower_target_resolution)
        new_coords = (int(low_res_coords[0] / factor),
                      int(low_res_coords[1] / factor))

        return new_coords

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

    def crop_img_by_percentage_coords(self, shape, percentageW = 1.0, percentageH = 1.0):
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

        return start,end

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
    def __init__(self,config):
        self.config = config
        self.debug = self.config['debug_mode']
        self.rate = self.config['average_refresh_rate']
        if self.debug:
            try:
                os.mkdir('debug')
            except FileExistsError:
                pass


    def fish_loop(self):
        print('Ready!')
        while(True):

            #wait for game window and cast at low frequency
            while(True):
                try:
                    self.image_ops = ImageOperations(self.config)
                except:
                    if self.debug:
                        if self.config['clear_screen']:
                            os.system('cls')
                        print("failed to init image operations class. it's normal if game is minimized.")
                    sleep(self.config['standby_sleep_time'])
                    continue

                #wait for cast
                start, end = self.image_ops.crop_img_by_percentage_coords(self.image_ops.game_window_res[::-1],-1 / 4, -1 / 5)
                lower_right_rect = (start[0],start[1],end[0] - start[0], end[1] - start[1])
                lower_right = self.image_ops.get_game_screen(lower_right_rect)
                adjusted_lower_right = self.image_ops.img_to_bw(self.image_ops.adjust_contrast(3, lower_right), 200)
                result = self.image_ops.locate_template(adjusted_lower_right, self.image_ops.hook_template_resized_to_game)
                if self.debug:
                    if self.config['clear_screen']:
                        os.system('cls')
                    debug_out = (self.image_ops.parent_area_coords(start, result[0]), result[1])
                    print('hook icon position and fitness:' + str(debug_out))
                if result[1] < self.config['templates_match_threshold']['hook_threshold']:
                    sleep(self.config['standby_sleep_time'])
                    continue
                else:
                    coords_to_game_screen = self.image_ops.parent_area_coords(start, result[0])
                    core_icon_rect = self.image_ops.expand_rect((*coords_to_game_screen,*self.image_ops.hook_template_resized_to_game.shape[:2][::-1]),
                        *map(lambda x:x * self.image_ops.get_scale_factor_preserve_ratio(self.config['templates_source_resolution'],
                                                                       self.image_ops.game_window_res),config['core_icon_expand_relative']))
                    if self.config['clear_screen']:
                        os.system('cls')
                    print('Rod casted!')
                    break

            #wait for bite or cancel
            while(True):
                core_icon_area = self.image_ops.get_game_screen(core_icon_rect)
                adjusted_icon = self.image_ops.img_to_bw(self.image_ops.adjust_contrast(3, core_icon_area), 200)
                wait = self.image_ops.locate_template(adjusted_icon, self.image_ops.hook_template_resized_to_game)[
                               1] > self.config['templates_match_threshold']['hook_threshold']
                if not wait:
                    break

            #determine whether bit or cancelled
            timeout_t1 = time()
            cancelled = False
            while (True):
                core_icon_area = self.image_ops.get_game_screen(core_icon_rect)
                adjusted_icon = self.image_ops.img_to_bw(self.image_ops.adjust_contrast(3, core_icon_area), 200)
                bit = self.image_ops.locate_template(adjusted_icon, self.image_ops.pull_template_resized_to_game)[1] >\
                      self.config['templates_match_threshold']['pull_threshold']
                if bit:
                    if self.config['clear_screen']:
                        os.system('cls')
                    print('You got a bite!')
                    break
                else:
                    timeout_t2 = time()
                    if timeout_t2 - timeout_t1 > self.config['wait_for_bite_timeout']:
                        if self.config['clear_screen']:
                            os.system('cls')
                        print('Cancelled')
                        cancelled = True
                        break

            if cancelled:
                continue

            self.mouse_down()
            #give the UI some time to pop up
            sleep(self.config['wait_for_progress_bar_time'])
            self.mouse_up()

            #find progress bar, assuming size can be calculated, x is always centered, y is the same as cursor center
            dim = self.image_ops.game_window_res
            crop_rect = (int(dim[0] * 3 / 10), 0, int(dim[0] * 4 / 10), int(dim[0] / 4))
            while(True):
                upper_center_area = self.image_ops.get_low_res_game_screen(crop_rect)#need progress bar coords in original size
                adjusted_upper_center_area = self.image_ops.get_progress_indicator_bw(upper_center_area)
                cursor_prefind = self.image_ops.locate_template(adjusted_upper_center_area,self.image_ops.cursor_template_resized_to_lower)
                if cursor_prefind[1] < self.config['templates_match_threshold']['cursor_threshold']:
                    if self.config['clear_screen']:
                        os.system('cls')
                    print('Failed to locate progress bar, retrying...')
                    continue
                else:
                    original_coords = self.image_ops.low_res_to_high_res_coords(cursor_prefind[0],upper_center_area.shape,crop_rect[2:4][::-1])
                    progress_bar_area_rect = (int((self.image_ops.game_window_res[0] - self.image_ops.progress_bar_template_resized_to_game.shape[1]) / 2),
                                              int(self.image_ops.anchor_to_center(self.image_ops.cursor_template_resized_to_game,original_coords)[1] -
                                              self.image_ops.progress_bar_template_resized_to_game.shape[0] / 2),
                                              int(self.image_ops.progress_bar_template_resized_to_game.shape[1] +
                                 self.image_ops.get_scale_factor_preserve_ratio(
                                     self.config['templates_source_resolution'],
                                     self.image_ops.lower_target_resolution) * config['progress_bar_expand_relative'][0])
                                 ,
                                 int(self.image_ops.progress_bar_template_resized_to_game.shape[0] +
                                     self.image_ops.get_scale_factor_preserve_ratio(
                                         self.config['templates_source_resolution'],
                                         self.image_ops.lower_target_resolution) *
                                     config['progress_bar_expand_relative'][1])
                                 )
                    break

            start_control_time = time()
            cycle_counter = 0
            #start controlling
            if not self.config['clear_screen']:
                print("Controlling...")
            while(True):
                if self.config['clear_screen']:
                    os.system('cls')
                    print("Controlling...")
                if keyboard.is_pressed('k'):
                    print('Interrupted!')
                    break

                cycle_counter +=1
                progress_bar_area = self.image_ops.get_low_res_game_screen(progress_bar_area_rect)
                adjusted_progress_bar_area = self.image_ops.get_progress_indicator_bw(progress_bar_area)

                #try to locate arrow and cursor
                try:

                    arrow_l = self.image_ops.locate_template(adjusted_progress_bar_area, self.image_ops.arrow_left_template_resized_to_lower)
                    arrow_r = self.image_ops.locate_template(adjusted_progress_bar_area, self.image_ops.arrow_right_template_resized_to_lower)
                    cursor = self.image_ops.locate_template(adjusted_progress_bar_area, self.image_ops.cursor_template_resized_to_lower)

                    if self.debug:
                        print('arrow_l/arrow_r/cursor position and fitness:' +
                              str((self.image_ops.parent_area_coords(progress_bar_area_rect[:2], arrow_l[0]), arrow_l[1])) + '\t'
                              + str((self.image_ops.parent_area_coords(progress_bar_area_rect[:2], arrow_r[0]), arrow_r[1])) + '\t'
                              + str((self.image_ops.parent_area_coords(progress_bar_area_rect[:2], cursor[0]), cursor[1])))

                    if arrow_l[1] < self.config['templates_match_threshold']['arrow_L_threshold'] or \
                            arrow_l[1] < self.config['templates_match_threshold']['arrow_R_threshold'] or  \
                            cursor[1] < self.config['templates_match_threshold']['cursor_threshold']:
                        raise Exception("Couldn't locate indicators")

                    #incase overlap
                    if cursor[1] > self.config['arrow_cursor_overlap_threshold']['cursor_clear']:
                        if arrow_l[1] < self.config['arrow_cursor_overlap_threshold']['arrow_L_overlap']:
                            arrow_l = cursor
                        if arrow_r[1] < self.config['arrow_cursor_overlap_threshold']['arrow_R_overlap']:
                            arrow_r = cursor


                except Exception:
                    core_icon_area = self.image_ops.get_game_screen(core_icon_rect)
                    adjusted_icon = self.image_ops.img_to_bw(self.image_ops.adjust_contrast(3, core_icon_area), 200)
                    finished = self.image_ops.locate_template(adjusted_icon, self.image_ops.pull_template_resized_to_game)[1] < self.config['templates_match_threshold']['pull_threshold']
                    if self.config['clear_screen']:
                        os.system('cls')
                    if finished:
                        print('Done fishing!')
                        break
                    else:
                        print("Lost track of indicators, retrying!")
                        continue

                if self.config['visualize']:
                    self.visualize(progress_bar_area_rect[0], progress_bar_area_rect[0] + self.image_ops.progress_bar_template_resized_to_lower.shape[1],
                                   arrow_l[0][0],
                                arrow_r[0][0], cursor[0][0])

                center_between_arrows_x = (arrow_l[0][0] + arrow_r[0][0]) / 2

                if cursor[0][0] < center_between_arrows_x:
                    self.click()
                else:
                    sleep(self.config['update_sleep_time'])

            finish_control_time = time()
            if self.rate:
                try:
                    print('average refresh rate in the last fishing session:' + str(cycle_counter / (finish_control_time - start_control_time)))
                except:
                    print('failed to print average refresh rate')

    def visualize(self, start, end, l, r, cursor):
        total_characters = 20
        full = end - start
        l_perc = l / full
        r_perc = r / full
        c_perc = cursor / full

        left_fill = int(l_perc * total_characters)
        mid_blank = int(r_perc * total_characters) - left_fill - 1
        right_fill = total_characters - left_fill - mid_blank - 1
        string = left_fill * '-' + '<' + mid_blank * ' ' + '>' + right_fill * '-'
        cursor_pos = int(c_perc * total_characters)
        new_string = string[:cursor_pos] + 'I' + string[cursor_pos + 1:]
        print(new_string)


    def click(self):

        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        sleep(self.config['update_sleep_time'])
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

    def mouse_down(self):
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)

    def mouse_up(self):
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,  0, 0)

if __name__ == '__main__':
    with open('config.json', 'r', encoding='utf-8') as config_file:
        config = json.load(config_file)
    clicker = Clicker(config)
    clicker.fish_loop()


