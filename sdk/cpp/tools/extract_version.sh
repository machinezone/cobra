#/bin/sh

grep VERSION ixcobra/ixcobra/IXCobraVersion.h | awk '{print $3}' | tr -d \"
