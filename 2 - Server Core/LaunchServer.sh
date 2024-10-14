#!/bin/bash

# When setting the memory below make sure to include the amount of ram letter. M = MB, G = GB. Don't use 1GB for example, it's 1G
MEMORY="32G"

# The path to the Java to use. Wrap in double quotes ("/opt/jre-17/bin/java"). Use "java" to point to system default install.
JAVAPATH="java"

# Any additional arguments to pass to Java such as Metaspace, GC or anything else
JVMARGS=""

# Don't edit past this point

cd "$(dirname "$0")"

LAUNCHARGS="$@"
# Launcher can specify path to java using a custom token
if [ "$1" = "ATLcustomjava" ]; then
    LAUNCHARGS="${@:2}"

    echo "Using launcher provided Java from $2"
    JAVAPATH="$2"
fi

echo
echo "Printing Java info below, if the Java version doesn't show below, your Java path is incorrect"
echo -----------------------
echo Java path is $JAVAPATH
$JAVAPATH -version
echo

FINALJAVAARGS="-Xmx$MEMORY $JVMARGS  "
FINALJAVAARGS=$(echo $FINALJAVAARGS | xargs echo -n)

if [ -f "server.jar" ]; then
    echo Using NeoForge ServerStarterJar, resetting user_jvm_args.txt contents
    echo

    echo "# DO NOT EDIT THIS FILE, IT IS AUTO GENERATED BY LaunchServer.bat/sh" >user_jvm_args.txt
    echo "# TO MAKE CHANGES TO RAM OR JVM ARGUMENTS, EDIT LaunchServer.bat/sh" >>user_jvm_args.txt
    echo $FINALJAVAARGS >>user_jvm_args.txt

    $FINALJAVAARGS=
fi

echo Launching below command
echo -----------------------
echo $JAVAPATH $FINALJAVAARGS -jar server.jar "$LAUNCHARGS"
echo
$JAVAPATH $FINALJAVAARGS -jar server.jar "$LAUNCHARGS"
read -n1 -r -p "Press any key to close..."
