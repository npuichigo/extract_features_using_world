#!/bin/sh

# tools directory
world="$(dirname $(dirname $(pwd)))/tools/bin/World"
sptk="$(dirname $(dirname $(pwd)))/tools/bin/SPTK-3.9"
reaper="$(dirname $(dirname $(pwd)))/tools/bin/REAPER"

# Output features directory
in_dir=$(dirname $(pwd))/1.extract_features
out_dir=$(pwd)

mgc_dir="${in_dir}/mgc"
bap_dir="${in_dir}/bap"
lf0_dir="${in_dir}/lf0_world"
resyn_dir="${out_dir}/resyn_dir"
resyn_wav_dir="${out_dir}/resyn_wav"

mkdir -p ${resyn_dir}
mkdir -p ${resyn_wav_dir}

# initializations
fs=16000

if [ "$fs" -eq 16000 ]
then
nFFTHalf=1024 
alpha=0.58
fi

if [ "$fs" -eq 48000 ]
then
nFFTHalf=2048
alpha=0.77
fi

mcsize=59
order=4

for file in $mgc_dir/*.mgc #.mgc
do
    filename="${file##*/}"
    file_id="${filename%.*}"

    echo $file_id

    ### WORLD Re-synthesis -- reconstruction of parameters ###

    ### convert lf0 to f0 ###
    $sptk/sopr -magic -1.0E+10 -EXP -MAGIC 0.0 ${lf0_dir}/$file_id.lf0 | $sptk/x2x +fa > ${resyn_dir}/$file_id.resyn.f0a
    $sptk/x2x +ad ${resyn_dir}/$file_id.resyn.f0a > ${resyn_dir}/$file_id.resyn.f0

    ### convert mgc to sp ###
    $sptk/mgc2sp -a $alpha -g 0 -m $mcsize -l $nFFTHalf -o 2 ${mgc_dir}/$file_id.mgc | $sptk/sopr -d 32768.0 -P | $sptk/x2x +fd > ${resyn_dir}/$file_id.resyn.sp

    ### convert bap to ap ###
    $sptk/mgc2sp -a $alpha -g 0 -m $order -l $nFFTHalf -o 2 ${bap_dir}/$file_id.bap | $sptk/sopr -d 32768.0 -P | $sptk/x2x +fd > ${resyn_dir}/$file_id.resyn.ap

    $world/synthesis ${resyn_dir}/$file_id.resyn.f0 ${resyn_dir}/$file_id.resyn.sp ${resyn_dir}/$file_id.resyn.ap ${resyn_wav_dir}/$file_id.resyn.wav
done

rm -rf $resyn_dir
