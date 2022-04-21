Todo List:

Important:
* Work on making the logo design
  * This will require making some sort of data blob buffer in the opencl kernel. My idea was to load all of the floats into a big array, and generate name-to-offset mapping through a list of #define directives.
* Finish Licensing part of readme
Less Important:
* Work on making integrating custom shaders easier
* Add animation to shaders through updating a global frameCount variable. Ignore this value on export, or allow option to set which frame is exported.
