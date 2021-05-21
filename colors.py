""" Colors
Written by Yona Edell
yona_edell@yahoo.com

This program creates and displays random RGB images (and uses multiple processes).
User specifies number of images to generate & dimensions.
User can press <Enter> key to view next image, or <q> key to quit.

Dependencies:
  - numpy
  - opencv-python
"""

import numpy as np
import multiprocessing as mp
import cv2, random, time
from collections import UserDict
from queue import Empty
# import logging
# from multiprocessing import log_to_stderr, get_logger

class TwoWayDict(UserDict):
    # Bi-directional dictionary, key maps to value and value maps to key
    # Saves me from using a loop to find a key/color name matching an (R,G,B) tuple
    # https://treyhunner.com/2019/04/why-you-shouldnt-inherit-from-list-and-dict-in-python/
    def __delitem__(self, key):
        value = self.data.pop(key)
        self.data.pop(value, None)
    def __setitem__(self, key, value):
        if key in self:
            del self[self[key]]
        if value in self:
            del self[value]
        self.data[key] = value
        self.data[value] = key

RGB_COLORS = TwoWayDict({
    'black'   : (0,0,0),
    'white'   : (255,255,255),
    'red'     : (255,0,0),
    'yellow'  : (255,255,0),
    'lime'    : (0,255,0),
    'aqua'    : (0,255,255),
    'blue'    : (0,0,255),
    'fuchsia' : (255,0,255)
})

def get_complement_color(rgb_arr:np.array) -> list:
    """Returns complement of RGB color (numpy array) by subtracting it from (255,255,255)"""
    return np.subtract((255,255,255), rgb_arr).tolist()

def generate_rgb_images(num_images:mp.Value, width:mp.Value, height:mp.Value,
                       queue_a:mp.Queue, event_quit:mp.Event):
    """ 
    Generates RGB images from randomly selected colors
    - num_images: desired number of RGB images to create
    - width: desired image width (in pixels)
    - height: desired image height (in pixels)
    - queue_a: output queue where created images are put
    - event_quit: event signal to stop upon shutdown
    
    Return values: None
    """
    i = num_images.value
    while i > 0 and not event_quit.is_set():
        rand_color = random.choice([*RGB_COLORS]) # selects a random color
        # Make sure we grabbed a str from the COLORS dict (and not tuple)
        if isinstance(rand_color, tuple):
            rand_color = RGB_COLORS[rand_color]
        # print(f"{rand_color} added to queue_a")
        # generate RGB image with random color and user-specified width/height
        rgb_image = np.full((height.value, width.value, 3), 
                            RGB_COLORS[rand_color], dtype=np.uint8)
        
        queue_a.put(rgb_image, timeout=1) 
        i -= 1
    queue_a.put(None, timeout=1) # sentinel value at end of queue_a to check

def watermark_images(queue_a:mp.Queue, queue_b:mp.Queue, event_quit:mp.Event):
    """
    Gets images from queue_a, draws circle & text on them, and puts onto queue_b
    Uses OpenCV to watermark image with name of color & filled circle in center
    Complementary colors are used for text/circle fill
    - queue_a: input queue, where images are read from
    - queue_b: output queue, where watermarked images are written to
    - event_quit: event signal to stop upon shutdown

    Return values: None
    """
    while not event_quit.is_set():
        rgb_image = queue_a.get(timeout=1) # waits 1 second for image on queue_a
        # Make sure queue_a isn't empty - according to docs, empty() not reliable:
        # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Queue
        if rgb_image is None: break # reached end of queue_a

        # Calculate circle attributes
        img_height, img_width = rgb_image.shape[:2]
        center = (img_width//2, img_height//2)
        radius = min(img_height, img_width) // 4
        comp_color = get_complement_color(rgb_image[0][0])
        # Draw circle on rgb_image
        cv2.circle(rgb_image, center, radius, comp_color, thickness=cv2.FILLED)

        # Get name of color for text
        img_text = RGB_COLORS[tuple(rgb_image[0][0])]
        # print(f"popped {img_text} from queue_a")
        
        # Scale text to appropriate size for different image dimensions
        text_scale = radius / 60
        text_thickness = int(radius / 40)
        
        # Get boundary of img_text
        text_size = cv2.getTextSize(img_text, cv2.FONT_HERSHEY_DUPLEX,
                                    text_scale, text_thickness)[0]
        
        # get coordinates based on boundary
        text_x = (img_width - text_size[0]) // 2 
        text_y = ((img_height - text_size[1]) // 2) - radius
        
        # add text to image aligned with center
        cv2.putText(rgb_image, text=img_text, org=(text_x, text_y), 
                    fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=text_scale,
                    color=comp_color, thickness=text_thickness)

        queue_b.put(rgb_image,timeout=1) # add watermarked image to queue_b
    queue_b.put(None,timeout=1) # sentinel value at end of queue_b to check

def display_image(array_a:mp.Array, event_start:mp.Event, event_quit:mp.Event,
                  event_next_img:mp.Event, width:mp.Value, height:mp.Value):
    """
    Continually reads from array_a & displays image w/ OpenCV.imshow()
    Waits for <q> key press to close window or <ENTER> to display next image
    - array_a: shared memory that contains single image to display
    - event_start: event signal to indicate when array_a has an image
    - event_quit: event signal to stop upon shutdown
    - event_next_img: event signal to display next image
    - width: image width (in pixels)
    - height: image height (in pixels)
    
    Return values: None
    """
    # TODO: get rid of this, I feel like I could make due with fewer event signals...
    event_start.wait() # waits/blocks until array_a has an image
        
    while not event_quit.is_set():
        with array_a.get_lock():
            # reads image from array_a as np.ndarray with C type unsigned int
            image = np.frombuffer(array_a.get_obj(), dtype="I"
                                 ).reshape(height.value, width.value, 3)
            color_text = RGB_COLORS[tuple(image[0][0])]
            # converts RGB image to BGR for OpenCV and displays image in new window
            cv2.imshow(f"Random Color Image Viewer",
                       cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_BGR2RGB))

            print(f"Image viewer showing: {color_text}")
            print(f"Press <Enter> to view next image or 'q' to quit...")

        key = cv2.waitKey(0)
        if key == ord('q'): # if 'q' is pressed, quit
            event_quit.set()
            event_next_img.set()
            break
        elif key == 13: # if <ENTER> key is pressed, go to next image
            event_next_img.set()
            print("\n*********\n <Enter> key pressed \n*********\n")
            # TODO: eliminate this sleep function! 
            time.sleep(0.01) # Atm, necessary to block to synchronize with other process.
                             # This makes sure the next image is displayed immediately
                             # after pressing <ENTER> once (instead of twice).
            
def get_valid_input(prompt:str, type_=None, min_=None):
    """
    Gets input from user and Returns validated/sanitized input
     - prompt: text displayed on console for prompting user input
     - type_: required, desired type for user input
     - min_: optional, required minimum for user input
    
    Taken from here: https://stackoverflow.com/a/23294659/14318152
    """
    while True:
        user_input = input(prompt)
        
        if type_ is not None:
            try:
                user_input = type_(user_input)
            except ValueError:
                print(f"Invalid input! Input must be of type {type_.__name__}\n")
                continue
            
            if min_ is not None and user_input < min_:
                print(f"Input must be greater than or equal to {min_}\n")
            
            else:
                return user_input

def cleanup(queue_a:mp.Queue, queue_b:mp.Queue, process_list:list):
    """
    Helper function to purge queues for clean exit upon shutdown
    From the docs: "if a child process has put items on a queue, then
    that process will not terminate until all buffered items have been
    flushed to the pipe."
    https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Queue
    """
    # Cleanup in case queues still have data, must be flushed for clean exit
    print("-"*58)
    print("Cleaning up, this will take just a sec...")
    count = 0
    # TODO: refactor this to be DRY
    while True:
        try:
            queue_b.get(block=False, timeout=0.01)
            count += 1
        except Empty:
            pass
        try:
            queue_a.get(block=False, timeout=0.01)
            count += 1
        except Empty:
            pass
        all_exited = True
        for p in process_list:
            if p.exitcode is None:
                all_exited = False
                break
        if all_exited and queue_b.empty() and queue_a.empty():
            break
    
    print("-"*58)
    print(f"Successful shutdown after flushing {count} items from memory!")
    print("_"*58)

if __name__== "__main__":
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("<     Random Image Creator & Viewer     >")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")

    num_images = get_valid_input("Enter number of images to generate: ", int, 1) 
    width = get_valid_input("Enter number of pixels for image width: ", int, 1) 
    height = get_valid_input("Enter number of pixels for image height: ", int, 1) 

    num_images = mp.Value('I', num_images) # convert to unsigned int types for multiprocessing
    width = mp.Value('I', width)   # convert to unsigned int types for multiprocessing
    height = mp.Value('I', height) # convert to unsigned int types for multiprocessing

    # generated images put here, watermark function gets from here 
    queue_a = mp.Queue() # used to pass image after generated to watermark function
    queue_b = mp.Queue() # images put here after watermarking

    # final images stored in this array for display
    array_a = mp.Array('I', width.value*height.value*3) 

    event_quit = mp.Event() # signals program completion/shutdown
    event_start= mp.Event() # signals when array_a is first populated

    event_next_img = mp.Event() # signals when ready to display next image
    event_next_img.set()        # turn on

    # log_to_stderr()
    # logger = get_logger()
    # # logger.setLevel(multiprocessing.SUBDEBUG)
    # logger.setLevel(logging.INFO)

    p_one = mp.Process(target=generate_rgb_images, 
                             args=(num_images,width,height,queue_a, event_quit))
    p_two = mp.Process(target=watermark_images, 
                            args=(queue_a,queue_b,event_quit))
    p_three = mp.Process(target=display_image,args=(array_a,event_start,
                                     event_quit,event_next_img,width,height))
    
    p_one.start()
    p_two.start()
    p_three.start()
    # TODO: maybe use mp.Condition? (same as threading.condition)
    # Continually read from queue_b and write to array_a
    while not event_quit.is_set():
        # print("Main() waiting for <ENTER> key to be pressed...")
        event_next_img.wait() # wait until ready for next image
        # if next.is_set():
        image = queue_b.get() # waits indefinitely for item in queue_b
        if image is None: # reached end of queue_b
            # This is to auto-quit window after pressing <ENTER> on last image
            event_quit.set() # comment out if want window to force you to press q to quit
            break
        # print(f"Main() - queue_b.get():{image[0][0]}")
        with array_a.get_lock():
            # print("Inside Main() lock")
            # Get contents of array_a
            arr = np.frombuffer(array_a.get_obj(), dtype="I"
                               ).reshape(height.value,width.value,3)
            arr[:] = image # Write image from queue_b to array_a
            event_start.set() # Used just on first run to make sure array_a is nonempty
            event_next_img.clear() # synchronizes to wait until ready for next image

    cv2.destroyAllWindows()

    cleanup(queue_a, queue_b, [p_one, p_two, p_three])

    p_one.join()
    p_two.join()
    p_three.join()
