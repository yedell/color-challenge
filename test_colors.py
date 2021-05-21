""" Test Colors
Written by Yona Edell
yona_edell@yahoo.com

This file uses pytest to execute unit tests
for all functions in colors.py

Dependencies:
  - numpy
  - opencv-python
  - pytest
"""

import pytest, colors 
from _mock_helper import set_keyboard_input, get_display_output # for mocking user input
import numpy as np
from multiprocessing import Value, Queue, Event

@pytest.mark.parametrize("input,expected", [
    ([0,0,0], [255,255,255]), # complement of white should be black
    ([0,255,0], [255,0,255]), # complement of green should be fuchsia
    ([255,0,0], [0,255,255])  # complement of red should be aqua
])
def test_get_complement_color(input,expected):
    """Gets complementary colors for example inputs and checks
       they match expected complementary colors"""
    output = colors.get_complement_color(np.array(input))
    assert output == expected 


@pytest.mark.parametrize("exp_num_images,width,height,queue_a,event_quit", [
    (Value("I",100), Value("I", 8), Value("I", 6), Queue(), Event()),
    (Value("I",50), Value("I", 246), Value("I", 379), Queue(), Event()),
    (Value("I",5), Value("I", 2470), Value("I", 1569), Queue(), Event())
])
def test_generate_rgb_images(exp_num_images,width,height,queue_a,event_quit):
    """Goes through every image output by generate function and checks
       expected dimensions & number of output images is correct.
       Also checks that the upper-left most pixel is in RGB_COLORS dict.
    """
    # TODO: incorporate event_quit, test currently overlooks this
    num_images_generated = 0
    colors.generate_rgb_images(exp_num_images,width,height,queue_a,event_quit)
    
    # loop through each image produced by function (stored in queue_a)
    # not using condition here to make sure queue gets flushed
    while True:
        img = queue_a.get(timeout=1)
        if img is None: break
        num_images_generated += 1

        # Check image has expected dimensions
        assert img.shape == (height.value,width.value,3)
        # Check that the color of upper-left most pixel is in RGB_COLORS dict
        assert tuple(img[0][0]) in colors.RGB_COLORS
    
    # Check if we generated the number of images we expected
    assert num_images_generated == exp_num_images.value


def test_watermark_images():
    """Goes through every image ouput by watermark function and compares
       for exact match with expected images. Uses example_generated_images.npz
       and example_watermarked_images.npz to accomplish this.
    """
    queue_a = Queue()
    queue_b = Queue()
    event_quit = Event()

    # Populate queue_a with RGB images from sample file
    input_images = np.load("example_generated_images.npz")
    for output_image in input_images:
        queue_a.put(input_images[output_image], timeout=1)
    queue_a.put(None, timeout=1) # must put sentinel to indicate end

    colors.watermark_images(queue_a, queue_b,event_quit)
    num_images_watermarked = 0
    i = 0

    # comparing output of watermark_images function to these images
    expected_images = np.load("example_watermarked_images.npz")
    # TODO: refactor below so don't need to list out names
    # using this list to iterate over each image in same loop
    array_names = 'arr_0 arr_1 arr_2 arr_3 arr_4 arr_5 arr_6 arr_7 arr_8 arr_9'.split()

    # loop through each image produced by function (stored in queue_b)
    # not using condition here to make sure queue gets flushed
    while True:
        output_image = queue_b.get(timeout=1)
        if output_image is None: break
        num_images_watermarked += 1
        
        # checking if output watermarked image exactly matches expected watermarked image
        assert (output_image==expected_images[array_names[i]]).all() == True
        i += 1
    
    # Check if we watermarked the expected number of images
    assert num_images_watermarked == len(expected_images)


@pytest.mark.parametrize("num_a_items,num_b_items", [
    (0,0),
    (0,37),
    (264,85),
    (639,639),
    (3,4831)
])
def test_cleanup(capsys, num_a_items, num_b_items):
    """Populates queues with dummy items and checks stdout
       to see if expected number of items got flushed"""
    queue_a = Queue()
    queue_b = Queue()

    for i in range(num_a_items):
        queue_a.put(i)
    queue_a.put(None,timeout=1)

    for i in range(num_b_items):
        queue_b.put(i)
    queue_b.put(None,timeout=1)

    colors.cleanup(queue_a,queue_b,[])
    out, err = capsys.readouterr()
    
    exp_total = num_a_items + num_b_items + 2 # expected number of items flushed from queue
    expected_output = ("----------------------------------------------------------\n"
                       "Cleaning up, this will take just a sec...\n"
                       "----------------------------------------------------------\n"
                       f"Successful shutdown after flushing {exp_total} items from memory!\n"
                       "__________________________________________________________\n")
    
    assert out == expected_output
    assert queue_a.empty() and queue_b.empty()


@pytest.mark.parametrize("input_list,prompt,type_,min_,expected", [
    (["fdafhf"],"Enter str",str,None,["Enter str"]),
    (["a word",-10.1,6],"Enter int >= 4",int,4,['Enter int >= 4', 'Invalid input! Input must be of type int\n', 'Enter int >= 4', 'Input must be greater than or equal to 4\n', 'Enter int >= 4']),
    (['y', -4],"hello",float,None,['hello', 'Invalid input! Input must be of type float\n', 'hello'])
])
def test_get_valid_input(input_list,prompt,type_,min_,expected):
    """Checks various valid & invalid input types 
      and compares to expected output. This test goes last
      since it messes with stdin/stdout."""

    set_keyboard_input(input_list)
    colors.get_valid_input(prompt,type_,min_)
    output = get_display_output()
    assert output == expected