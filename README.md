# \<AI Startup\> Programming Challenge
### Author: Yona Edell

A random RGB image generator that creates & displays images using
 [`multiprocessing`](https://docs.python.org/3/library/multiprocessing.html), 
 [`numpy`](https://numpy.org/), and 
 [`opencv`](https://pypi.org/project/opencv-python/).
Created as part of a timed programming challenge given only these [instructions](./instructions.pdf).

## Getting Started

- Written with `Python 3.8.8` 
    - will probably work with *Python 3.6+* (but don't hold me to that 😛)
- Install dependencies: `pip install -r requirements.txt`

Run main program: 
```
python colors.py
```

Run tests:
```
pytest test_colors.py
```

## Usage

When running `colors.py`, you should see the following prompt on the command line:

```
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
<     Random Image Creator & Viewer     >
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Enter number of images to generate:
```

User is prompted for input to number of images to generate, image width, and image height.
Once the user submits the input, a new window opens to display the randomly generated RGB images. 
The user can press the <kbd>Enter</kbd> key to view the next image, 
or the <kbd>Q</kbd> key to quit the program.

*Bonus feature: text size & position watermarked on the image are relative(ish) to image dimensions/size!*


### **Important Notes:**
- Display/text/app scaling on your OS will affect this program's image viewing dimensions
    - turn off if you want to view large images at their true resolution;
      instructions for Windows 10 [here](https://www.lifewire.com/using-windows-10-display-scaling-4587328 "How to use Windows 10 Display Scaling")
- If you're viewing the last image and you press <kbd>Enter</kbd>
 (to view next image), the program will auto-quit
    - if this behavior is undesired, i.e. you'd like to be forced to press 
    <kbd>Q</kbd> to quit after the last image, comment out Line 282 in `colors.py`
- *The size of your RAM is the only real limit to how many images you can generate* ✨
    - that's right: I generated 100,000 500x500px images and let the program use 8GB+ of 
    my system's memory before pressing <kbd>Q</kbd>--it took ~30 seconds to flush
     the queues & completely shutdown, but it got there!

## Conclusion

I learned a ton throughout this project, especially since it was my first time using
`multiprocessing`, `opencv`, or `pytest` (I've only used the `unittest` library). I hit 
several snags along the way and spent too much time diagnosing race conditions & deadlocks 
and manually killing zombie/orphaned processes. The most challenging parts were keeping
`array_a` synchronized to view/get the images in order from `queue_b` and making a clean
exit when quitting before all queue items had been consumed. Honorable mentions go to
the [horse's ass](https://learnopencv.com/why-does-opencv-use-bgr-color-format/ "Why does OpenCV use BGR color format?") 
behind the `opencv` BGR color space choice  (this one got me good) and perpetually 
mixing up the width/height dimensions between the `numpy`, `multiprocessing`, 
and `opencv` arrays. 

As far as results go, I think the testing aspect has the most room
for improvement. I'm not satisfied with how much my simple/functional unit tests cover--
I left out a unit test for the `display_image()` function since it's inherently convoluted
(the best I could do would be checking that it terminates, but how much good is that?). 
I'd really like to refactor/clean up most of my tests (use fixtures, setup/teardowns, classes),
but I think I'll go to bed now! 😴

## To-do

- Refactor code to be more DRY, especially the tests
- Eliminate one of the multiprocessing Events; probably don't need `event_start`, could maybe use a Condition
- Use process pooling/queue managers or joinable queues so don't have to worry about queue flushing upon quit
- Add more test cases and different kinds of tests (performance, stress, end-to-end/integration, etc)
- Add more timeouts to shared objects (to be more defensive in preventing deadlocks)
- Add more/fancier colors!!!
- Add throttling or I/O caching functionality so memory doesn't get hogged when generating thousands of images
- Use threads instead of processes to reduce resource consumption & potentially add speedup (?)
- Make "auto-quit" feature (mentioned above in [Important Notes](#important-notes)) a command line option with `argparse`