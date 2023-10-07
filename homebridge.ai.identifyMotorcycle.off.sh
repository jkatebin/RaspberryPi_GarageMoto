#!/bin/bash

current_time=$(date "+%Y.%m.%d-%H.%M.%S")
rootFilePath="/home/jkatebin/motion_detected"

fileName=motion_detected.off.$current_time.txt

echo Creating $rootFilePath/$fileName

touch $rootFilePath/$fileName
