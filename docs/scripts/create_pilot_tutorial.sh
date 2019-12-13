#!/usr/bin/env bash

PILOT_COMMAND="pilot"
PILOT_TUTORIAL='pilot-tutorial'
FILES_DIR='supporting_files'

function PILOT {
  echo "------------- pilot $@ --------------"
  $PILOT_COMMAND $@
  if [ $? -ne 0 ]; then
    echo "Pilot Command failed, exiting..."
    exit 1
  fi
}

function upload_file {
  PILOT upload $@
  PSTATUS=$($PILOT_COMMAND status | head -n 3 | tail -n 1 | cut -c 35-43 | tr -d '[:space:]')
  echo "Status of Upload: $PSTATUS"
  while [ "$PSTATUS" == 'ACTIVE' ]; do
    PSTATUS=$($PILOT_COMMAND status | head -n 3 | tail -n 1 | cut -c 35-43 | tr -d '[:space:]')
    echo "Status of Upload: $PSTATUS"
  done
  echo "Upload '$1' Success."
}

VERSION=$($PILOT_COMMAND version)
echo "Running Project Creation on Pilot Version $VERSION"

PILOT login
PILOT project

CREATE_NEW_PROJECT=false
GET_PROJECT=$($PILOT_COMMAND project | grep $PILOT_TUTORIAL | cut -c 3-)
if [ "$GET_PROJECT" == "$PILOT_TUTORIAL" ]; then
  PILOT project set "$PILOT_TUTORIAL"
  PILOT list
  CONTENT=$($PILOT_COMMAND list | tail -n +2 | wc -l | awk '{print $1}')
  echo "Found $CONTENT records in project."
  if [ "$CONTENT" -eq "0" ]; then
    echo "$PILOT_TUTORIAL currently empty, keeping project."
  else
    echo "Existing records found, deleting and recreating project..."
    PILOT project delete "$PILOT_TUTORIAL"
    CREATE_NEW_PROJECT=true
  fi
else
CREATE_NEW_PROJECT=true
fi

if [ "$CREATE_NEW_PROJECT" == "true" ]; then
  echo "Suggested options:"
  echo "title               Pilot Tutorial"
  echo "short_name          $PILOT_TUTORIAL"
  echo "description         Guide to using the pilot CLI for managing and accessing data."
  echo "group               public"
  PILOT project add
fi

SELECTED_PROJECT=$($PILOT_COMMAND project | grep [*] | cut -c 3-)
if [ "$SELECTED_PROJECT" != "$PILOT_TUTORIAL" ]; then
  echo "Project not selected, something went wrong..."
  exit 1
else
  echo "Selected Project: '$SELECTED_PROJECT'"
  PILOT project info "$SELECTED_PROJECT"
fi

WEST_COAST_DIR="west_coast"
PILOT mkdir "$WEST_COAST_DIR"
upload_file "$FILES_DIR/chicago" "/" -j "$FILES_DIR/chicago_metadata.json"
upload_file "$FILES_DIR/ashland_skewt" "$WEST_COAST_DIR" -j "$FILES_DIR/ashland_plot_metadata.json"
upload_file "$FILES_DIR/san_diego_skewt" "$WEST_COAST_DIR" -j "$FILES_DIR/san_diego_plot_metadata.json"
upload_file "$FILES_DIR/new_york_skewt" "/" -j "$FILES_DIR/new_york_plot_metadata.json"
upload_file "$FILES_DIR/practical_meteorology" "/" -j "$FILES_DIR/practical_meteorology_metadata.json"

echo "Finished creating $SELECTED_PROJECT"