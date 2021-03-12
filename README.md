# LF - LabelFaster

![alt text][logo]

LabelFaster is an image label application, which allows to label images in a workflow, which uses the mouse and the keyboard at the same time. If you have a large image set to label, the time you need to label an image is a good reference for your overall performance. Maxing out the capabilities of using both of your hands in parallel, will increase your labelspeed enourmous.

Additional to the both supported Annotation formats Yolo and PascalVOC a third format is implemented which creates Box shaped Image SemanticSegmentation Labels for the [BoxSup](https://arxiv.org/abs/1503.01640) Algorithm.

## Installation

The related application was builded for [python2.6](https://www.python.org/downloads/release/python-269/) but will be supported for this application.

To create one and only one workflow the installation will be explained with the usage of a  virtual environment. If you want to use anaconda or other tools feel free to take a look at the related project.

### How to setup a venv?

The setup of a venv is very well described by the [python documentation](https://docs.python.org/3/tutorial/venv.html) and repeating lines from where will suppress informations, which might be helpful for you. 

It is recommended to install the following packages inside the activated venv, so commands ```python``` and ```pip``` will always use the correct version.

```bash
cd LabelFaster
pip install PyQt5
pip install lxml
pyrcc5 -o libs/resources.py resources.qrc
```

## Usage

## License

[GNU GPL](https://github.com/MaKaNu/ROISA-Region_of_Interest_Selector_Automat/blob/master/LICENSE)

## Related Project

[LabelImg](https://github.com/tzutalin/labelImg])

[logo]: https://raw.githubusercontent.com/MaKaNu/LabelFaster/master/resources/icons/Logo4_bg.png "Logo of LabelFaster App."
