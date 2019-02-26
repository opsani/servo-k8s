#!/bin/sh
echo $@
java $@ -XX:+PrintFlagsFinal -version && sleep 3600
