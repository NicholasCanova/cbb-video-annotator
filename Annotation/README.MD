# Annotation and Visualization Tools (Fork)

This repository is a fork of the SoccerNet-v2 Annotation and Visualization Tools
(https://github.com/SoccerNet/sn-spotting/tree/main)

The original tool was developed by researchers at:
* University of Liège (ULiège)
* King Abdullah University of Science and Technology (KAUST)
* Aalborg University (AAU)

This fork has been modified for a different annotation workflow and dataset
and is not affiliated with or maintained by the original authors.

## Changes in This Fork
* Updated environment setup (Python 3.8, venv instead of conda)
* Removed SoccerNet dataset dependency
* Added fast keyboard-driven annotation workflow
* Added event time adjustment and visualization improvements
* Modified label handling and output format


## Getting Started

The following instructions will help you install the required libraries and the dataset to run the tools. The code runs in <code>python 3.8</code> .

### Create environment

To create and setup the virtual environment, simply follow these steps:

```bash
# create a virtual environment using python 3.8
pyenv versions
pyenv local 3.8.19
python3.8 --version
python3.8 -m venv venv
source venv/bin/activate
#deactivate  # to deactivate the venv each time when done
pip install --upgrade pip
pip install pyqt5
```

## Run the tools

Once the environment is ready, you can simply run the annotation tool for action spotting with the following commands:

```bash
cd src/
python main.py
```


### Start the visualization

To start the visualization, click on the open video button at the bottom left of the annotator and select a video from the dataset (named 1.mkv or 2.mkv). The labels-v2.json (for actions) should be placed in the same folder as the video. A sample video and annotation file is placed in the "example video" folder.

Once the video is opened, you can easily navigate through it either using the time bar at the bottom or by double-clicking on the annotations in the right column. You can also navigate in the video frame by frame using the left and right arrow keys, or speed up the video using A (x1) Z (x2) E (x4) and pause or re-start the video with the SPACEBAR.

### Annotate your own actions

To annotate a new action, go to the exact frame you want to annotate, press ENTER (not the one on the numpad) and navigate through the menu.

To delete an annotation, double-click on it in the right column and press DELETE. 

## License

Apache v2.0
See the [LICENSE](LICENSE) file for details.
