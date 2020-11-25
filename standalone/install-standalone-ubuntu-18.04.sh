#!/bin/bash --

## Resolve the path to this script file
# Taken from https://stackoverflow.com/a/246128/400948
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
    DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
    SOURCE="$(readlink "$SOURCE")"
    # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
script_dir="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
curr_dir=$(pwd)

imiversion=$(cat "${script_dir}/../iminspect/version.py" | grep __version__ | awk '{split($0,a,"="); print a[2]}' | tr -d "\"[:space:]'")
echo "Installing iminspect v${imiversion}"

#echo "* Exporting SVG to PNG to create ICO"
#cd ${script_dir}/../iminspect/iminspect_assets
#highdpi_file=iminspect-300dpi.png
#inkscape --export-png=${highdpi_file} --export-area-page --export-dpi=300 iminspect.svg
#lowres_str=""
#for res in 16 24 32 48 64 72 96 128 256 512
#do
#  echo "Rendering icon size $res"
#  convert ${highdpi_file} -resize ${res}x${res} iminspect-${res}.png
#  lowres_str="${lowres_str} iminspect-${res}.png"
##  cp iminspect-${res}.png ~/.local/share/icons/hicolor/${res}x${res}/apps/iminspect.png
#done
#echo "${lowres_str}"
#convert ${lowres_str} iminspect.ico
#rm *.png

cd "${script_dir}"
venv_dir=iminspect_venv
if [[ ! -d "$venv_dir" ]]; then
    echo "* Creating virtual environment"
    python3 -m venv "${venv_dir}"
else
    echo "* Updating virtual environment"
fi
source "${venv_dir}"/bin/activate
pip install -U pip
pip install -U iminspect

# Replace path in launcher
imipath=${script_dir}/${venv_dir}

# Add executable to user's path
local_bin=~/.local/bin/iminspect
cp ${script_dir}/iminspect.sh.tpl "${local_bin}"
sed -i "s:IMIPATH:${imipath}:g" "${local_bin}"
chmod +x "${local_bin}"
echo "* Placed shell script: ${local_bin}"

# Set up app launcher for menu
app_launcher=~/.local/share/applications/iminspect.desktop
cp ${script_dir}/iminspect.desktop.tpl "${app_launcher}"
sed -i "s:IMIPATH:${imipath}:g" "${app_launcher}"
sed -i "s:IMIVERSION:${imiversion}:g" "${app_launcher}"

# Grab correct python version
pyfolder=$(ls -A "${venv_dir}"/lib | head -n 1)
sed -i "s/IMIPY/${pyfolder}/g" "${app_launcher}"

# Validate launcher
echo "* Created launcher file: ${app_launcher}"
desktop-file-validate "${app_launcher}"

cd "${curr_dir}"
