"""
Modified camshift tracker from opencv sample
"""
import math
import json
import socket
import cv

CAM_WINDOW = "CamShiftTracker"
HISTOGRAM_WINDOW = "Histogram"
STOP_CRITERIA = (cv.CV_TERMCRIT_EPS | cv.CV_TERMCRIT_ITER, 10, 1)
TARGET_ELLIPSE_COLOR = (255, 255, 0)
CENTROID_COLOR = (255, 0, 0)

def is_rect_nonzero(r):
    (_, _, w, h) = r
    return (w > 0) and (h > 0)

def get_hue_histogram_image(hist):
    """ Returns a nice representation of a hue histogram
    """
    histimg_hsv = cv.CreateImage((320, 200), 8, 3)

    mybins = cv.CloneMatND(hist.bins)
    cv.Log(mybins, mybins)
    (_, hi, _, _) = cv.MinMaxLoc(mybins)
    cv.ConvertScale(mybins, mybins, 255. / hi)

    w, h = cv.GetSize(histimg_hsv)
    hdims = cv.GetDims(mybins)[0]
    for x in range(w):
        xh = (180 * x) / (w - 1)  # hue sweeps from 0-180 across the image
        val = int(mybins[int(hdims * x / w)] * h / 255)
        cv.Rectangle(histimg_hsv, (x, 0), (x, h-val), (xh, 255, 64), -1)
        cv.Rectangle(histimg_hsv, (x, h-val), (x, h), (xh, 255, 255), -1)

    histimg = cv.CreateImage((320, 200), 8, 3)
    cv.CvtColor(histimg_hsv, histimg, cv.CV_HSV2BGR)
    return histimg

class CamShiftTracker:

    def __init__(self, camera=0, height=640, width=480):
        self.capture = cv.CaptureFromCAM(camera)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_WIDTH, height)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_HEIGHT, width)
        cv.NamedWindow(CAM_WINDOW, 1)
        cv.NamedWindow(HISTOGRAM_WINDOW, 1)
        cv.SetMouseCallback(CAM_WINDOW, self.on_mouse)
        #green
        self.target_x = 0
        self.target_y = 0
        #red
        self.tracker_center_x = 0
        self.tracker_center_y = 0
        self.drag_start = None      # Set to (x,y) when mouse starts drag
        self.track_window = None    # Set to rect when the mouse drag finishes
        self.selection = None
        self.drag_start2 = None      # Set to (x,y) when mouse starts drag
        self.track_window2 = None    # Set to rect when the mouse drag finishes
        self.selection2 = None        
        self.hue = None
        self.hue2 = None
        self.quit = False
        self.backproject_mode = False
        self.message = {}

        self.count = 0

        print("Keys:\n"
            "    ESC - quit the program\n"
            "    b - switch to/from backprojection view\n"
            "To initialize tracking, drag across the object with the mouse\n")

    def on_mouse(self, event, x, y, *args):
        if event in [cv.CV_EVENT_LBUTTONDOWN, cv.CV_EVENT_LBUTTONUP, cv.CV_EVENT_MOUSEMOVE]:
            self.left_mouse_click(event, x, y)
        if event in [cv.CV_EVENT_RBUTTONDOWN, cv.CV_EVENT_RBUTTONUP, cv.CV_EVENT_MOUSEMOVE]:
            self.right_mouse_click(event, x, y)

    def left_mouse_click(self, event, x, y):
        if event == cv.CV_EVENT_LBUTTONDOWN:
            self.drag_start = (x, y)
        elif event == cv.CV_EVENT_LBUTTONUP:
            self.drag_start = None
            self.track_window = self.selection

        if self.drag_start:
            xmin = min(x, self.drag_start[0])
            ymin = min(y, self.drag_start[1])
            xmax = max(x, self.drag_start[0])
            ymax = max(y, self.drag_start[1])
            self.selection = (xmin, ymin, xmax - xmin, ymax - ymin)
            
    def right_mouse_click(self, event, x, y):
        if event == cv.CV_EVENT_RBUTTONDOWN:
            self.drag_start2 = (x, y)
        elif event == cv.CV_EVENT_RBUTTONUP:
            self.drag_start2 = None
            self.track_window2 = self.selection2

        if self.drag_start2:
            xmin = min(x, self.drag_start2[0])
            ymin = min(y, self.drag_start2[1])
            xmax = max(x, self.drag_start2[0])
            ymax = max(y, self.drag_start2[1])
            self.selection2 = (xmin, ymin, xmax - xmin, ymax - ymin)    

    def run(self):
        hist = cv.CreateHist([180], cv.CV_HIST_ARRAY, [(0, 180)], 1)
        hist2 = cv.CreateHist([180], cv.CV_HIST_ARRAY, [(0, 180)], 1)
        HOST, PORT = 'localhost', 5000
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        while not self.quit:
            frame = cv.QueryFrame(self.capture)
            frame2 = cv.QueryFrame(self.capture)
            track_box = None
            track_box2 = None
            self.update_hue(frame)
            self.update_hue2(frame)

            # Compute back projection
            backproject = cv.CreateImage(cv.GetSize(frame), 8, 1)
            cv.CalcArrBackProject([self.hue], backproject, hist)
            if self.track_window and is_rect_nonzero(self.track_window):
                camshift = cv.CamShift(backproject, self.track_window, STOP_CRITERIA)
                (iters, (area, value, rect), track_box) = camshift
                self.track_window = rect
                
            backproject2 = cv.CreateImage(cv.GetSize(frame2), 8, 1)
            cv.CalcArrBackProject([self.hue2], backproject2, hist2)
            if self.track_window2 and is_rect_nonzero(self.track_window2):
                camshift2 = cv.CamShift(backproject2, self.track_window2, STOP_CRITERIA)
                (iters, (area, value, rect), track_box2) = camshift2
                self.track_window2 = rect
            
            if self.drag_start and is_rect_nonzero(self.selection):
                self.draw_mouse_drag_area(frame,self.selection)
                self.recompute_histogram(hist)
            elif self.track_window and is_rect_nonzero(self.track_window):
                cv.EllipseBox(frame, track_box, cv.CV_RGB(255, 0, 0), 3, cv.CV_AA, 0)
                
            if self.drag_start2 and is_rect_nonzero(self.selection2):
                
                self.draw_mouse_drag_area(frame2,self.selection2)
                self.recompute_histogram(hist2)
            elif self.track_window2 and is_rect_nonzero(self.track_window2):
                cv.EllipseBox(frame2, track_box2, cv.CV_RGB(0, 255, 0), 3, cv.CV_AA, 0)            

            if track_box:
                self.update_message(track_box)
                sock.send(json.dumps(self.message) + "\n")
            self.draw_target(frame, track_box)
            self.update_windows(frame, backproject, hist)
            self.draw_target2(frame2, track_box2)
            self.update_windows(frame2, backproject2, hist2)            
            self.handle_keyboard_input()
            track_box = None
            track_box2 = None

    def update_hue(self, frame):
        """ Convert frame to HSV and keep the hue
        """
        hsv = cv.CreateImage(cv.GetSize(frame), 8, 3)
        cv.CvtColor(frame, hsv, cv.CV_BGR2HSV)
        self.hue = cv.CreateImage(cv.GetSize(frame), 8, 1)
        cv.Split(hsv, self.hue, None, None, None)
        
    def update_hue2(self, frame):
        """ Convert frame to HSV and keep the hue
        """
        hsv = cv.CreateImage(cv.GetSize(frame), 8, 3)
        cv.CvtColor(frame, hsv, cv.CV_BGR2HSV)
        self.hue2 = cv.CreateImage(cv.GetSize(frame), 8, 1)
        cv.Split(hsv, self.hue2, None, None, None)    

    def draw_mouse_drag_area(self, frame,selection):
        """ Highlight the current selected rectangle
        """
        sub = cv.GetSubRect(frame, selection)
        save = cv.CloneMat(sub)
        cv.ConvertScale(frame, frame, 0.5)
        cv.Copy(save, sub)
        x, y, w, h = selection
        cv.Rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255))
        

    def recompute_histogram(self, hist):
        sel = cv.GetSubRect(self.hue, self.selection)
        cv.CalcArrHist([sel], hist, 0)
        (_, max_val, _, _) = cv.GetMinMaxHistValue(hist)
        if max_val != 0:
            cv.ConvertScale(hist.bins, hist.bins, 255. / max_val)

    def update_windows(self, frame, backproject, hist):
        if not self.backproject_mode:
            cv.ShowImage(CAM_WINDOW, frame)
        else:
            cv.ShowImage(CAM_WINDOW, backproject)
        cv.ShowImage(HISTOGRAM_WINDOW, get_hue_histogram_image(hist))

    def handle_keyboard_input(self):
        c = cv.WaitKey(7) % 0x100
        if c == 27:
            self.quit = True
        elif c == ord("b"):
            self.backproject_mode = not self.backproject_mode
       

    def draw_target(self, frame, track_box):
        if track_box:
            self.tracker_center_x = float(min(frame.width, max(0, track_box[0][0] - track_box[1][0] / 2)) + \
                    track_box[1][0] / 2)
            self.tracker_center_y = float(min(frame.height, max(0, track_box[0][1] - track_box[1][1] / 2)) + \
                    track_box[1][1] / 2)

            if not math.isnan(self.tracker_center_x) and not math.isnan(self.tracker_center_y):
                tracker_center_x = int(self.tracker_center_x)
                tracker_center_y = int(self.tracker_center_y)
                cv.Circle(frame, (tracker_center_x, tracker_center_y), 5, CENTROID_COLOR, 1)
                
                
    def draw_target2(self, frame, track_box):
        if track_box:
            self.target_x = float(min(frame.width, max(0, track_box[0][0] - track_box[1][0] / 2)) + \
                    track_box[1][0] / 2)
            self.target_y = float(min(frame.height, max(0, track_box[0][1] - track_box[1][1] / 2)) + \
                    track_box[1][1] / 2)

            if not math.isnan(self.target_x) and not math.isnan(self.target_y):
                tracker_center_x = int(self.target_x)
                tracker_center_y = int(self.target_y)
                cv.Circle(frame, (tracker_center_x, tracker_center_y), 5, CENTROID_COLOR, 1)



       

    def update_message(self, track_box):
        self.message['x'] = float(self.tracker_center_x)
        self.message['y'] = float(self.tracker_center_y)
        self.message['a'] = float(track_box[1][0]) * float(track_box[1][1])
        self.message['theta'] = float(track_box[2])
        self.message['targetx'] = float(self.target_x)
        self.message['targety'] = float(self.target_y)
        


if __name__ == "__main__":
    tracker = CamShiftTracker()
    tracker.run()
