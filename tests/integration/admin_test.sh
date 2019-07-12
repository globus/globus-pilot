#!/usr/bin/env bash

PILOT="pilot"
TEST_FILE='pilot-integration-testing-test-file.csv'
TEST_DIRECTORY='pilot-integration-testing-test-dir'

VERSION=$(PILOT version)
echo "Running Admin Tests for Pilot Version $VERSION"

echo "Initiating a fresh login..."
$PILOT logout
$PILOT login

$PILOT profile

$PILOT project add

SELECTED_PROJECT=$(PILOT project | grep [*] | cut -c 3-)
echo "SELECTED PROJECT DETECTED: '$SELECTED_PROJECT'"

$PILOT project info $SELECTED_PROJECT

echo "firstrow,secondrow,thirdrow,fourthrow,fifthrow,sixthrow,seventhrow,eighthrow,ninethrow,tenthrow,eleventhrow,twelthrow,thirtheenthrow" > $TEST_FILE
echo "firstrow,secondrow,thirdrow,fourthrow,fifthrow,sixthrow,seventhrow,eighthrow,ninethrow,tenthrow,eleventhrow,twelthrow,thirtheenthrow" >> $TEST_FILE
$PILOT mkdir $TEST_DIRECTORY
$PILOT upload $TEST_FILE $TEST_DIRECTORY

PSTATUS=$($PILOT status | head -n 3 | tail -n 1 | cut -c 35-43)
while [ $PSTATUS == 'ACTIVE' ]; do
  PSTATUS=$($PILOT status | head -n 3 | tail -n 1 | cut -c 35-43)
  echo "Status of Upload: $PSTATUS"
done
rm $TEST_FILE

echo -n "Pilot list... "
PLIST=$(PILOT list | grep $TEST_FILE)
OUTPUT=$(test "$PLIST")
if [[ $OUTPUT -eq 0 ]]; then echo "SUCCESS"; else echo "FAILURE"; fi

echo -n "Pilot describe... "
PLIST=$(PILOT describe $TEST_FILE | grep $TEST_FILE)
OUTPUT=$(test "$PLIST")
if [[ $OUTPUT -eq 0 ]]; then echo "SUCCESS"; else echo "FAILURE"; fi

$PILOT download "$TEST_DIRECTORY/$TEST_FILE"
rm $TEST_FILE

$PILOT delete "$TEST_DIRECTORY/$TEST_FILE"
$PILOT delete "$TEST_DIRECTORY"

$PILOT project delete $SELECTED_PROJECT

echo "Finished running through all pilot commands."