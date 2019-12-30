#!/bin/bash --

# Virtual environment
venv=.venv3
if [ ! -d "${venv}" ]
then
  echo "Setting up virtual environment"
  python3 -m venv ${venv}
  source ${venv}/bin/activate
  pip3 install --upgrade pip
  pip3 install -r requirements.txt
#  pip3 install pur
#  pur -r ../requirements.txt

  
  # Set up OpenCV - assumes that you already installed it!
#  echo "Trying to link to your OpenCV installation"
#  opencv_lib=$(find /usr -name cv2* | grep python3 | head -n 1)
#  if [ -z "${opencv_lib}" ]
#  then
#    echo "[E] You need to install OpenCV first!" 1>&2
#    exit 23
#  fi
#  # Get correct python subfolder
#  pverstring=$(ls ${venv}/lib/ | grep python3)
#  libdir=$(dirname "${opencv_lib}")
#  #echo $libdir
#  #echo $pverstring
#  # Create link file in virtualenv
#  echo ${libdir} > ${venv}/lib/${pverstring}/site-packages/cv2.pth  
fi

echo
echo "################################################################"
echo
echo "  Don't forget to activate your virtual environment:"
echo
echo "    source ${venv}/bin/activate"
echo
echo "################################################################"
echo

