if id -nG "$LOGNAME" | grep -qw "mswin"; then
   ../gfxlaunch.py --title "Windows Application" --partition win --account=lvis-test --simplified --only-submit --job=vm
else
   zenity --info --width=600 --height=300 --text="Welcome to LUNARC's Microsoft Windows 10 Interactive HPC Desktop\n\n\nSome Features:\n\n-- Windows applications can coexist with Linux applications in the same desktop\n\n-- Full 2D and 3D hardware graphics acceleration (NVIDIA V100 card)\n\n-- Seamless integration with center storage and Linux applications\n\n-- Scientific software are installed upon request (similar to Aurora)\n\n\nPlease contact LUNARC support (support@lunarc.lu.se) to get access to this feature"
fi



