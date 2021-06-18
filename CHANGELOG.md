# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [0.6.0](https://github.com/globusonline/pilot1-tools/compare/v0.5.0...v0.6.0) (2021-06-18)


### Features

* added .build_short_path to client for convenience ([8865102](https://github.com/globusonline/pilot1-tools/commit/886510201894a4b4e208cb98703d57ed2393864d))
* Added 'index setup' command, for setting up pilot ([e3a220c](https://github.com/globusonline/pilot1-tools/commit/e3a220cbb5a3c696fb244fe09fd0a21463c2e645))
* Added config-less option for running pilot ([efcac70](https://github.com/globusonline/pilot1-tools/commit/efcac70595fce112cf59f58aa219304cafbe3dc6))
* Project deletion is cleaner now ([ae9194d](https://github.com/globusonline/pilot1-tools/commit/ae9194ded9ea33cfbc1530421d4132919721ea00))


### Bug Fixes

* comparing updated projects with removed items ([36b15ef](https://github.com/globusonline/pilot1-tools/commit/36b15ef7d4f9b51c954a9f07bca3656a0b356be4))
* Disallow '~' in base index/project paths. These cause problems. ([4427e3c](https://github.com/globusonline/pilot1-tools/commit/4427e3cd4ac1e673f762f7de5865be4d74a507dd))
* Disallow 'setup' when projects exist ([446eb67](https://github.com/globusonline/pilot1-tools/commit/446eb672beea53b7b5310f4df517eec19ae59d59))
* Group default not properly being set on ingest ([5326308](https://github.com/globusonline/pilot1-tools/commit/5326308b94f7c4e4879eb76eb9f69732c6c70ad9))
* small fix for running in configless mode ([5a3bc6d](https://github.com/globusonline/pilot1-tools/commit/5a3bc6d4e5cac1675ea440ac61f916a8d88f5c41))

### 0.5.0 - 2021-04-13

 - Released on PyPi!
 - Renamed 'context' command to 'index'
 - Changed 'index/context' command to be public
 
 - Fixed config bug when setting index by UUID
 - Fixed exception in `project push` and `project edit` commands
 - Fixed regression, added test for improper file versioning
 - Fixed bug with version being reset when metadata changed but file didn't
 - Fixed Dry-run to properly generate change stats
 - Fixed search.files_modified returning None instead of False
 - Fixed string formatting on some exceptions
 - Fixed conda git lfs build error by switching to local builds
 - Fixed puremagic and fair-research-login build dependencies
 - Fixed diff not working for changes in context information on update
 - Fixed bug in pushing project/context info to Globus Search
 - Fixed bug with portal URL silently being not generated
 - Fixed non-ranged download exception
 - Fixed bug in `list` command not displaying more than 10 results
 - Fixed passing context to transfer command
 - Fixed portal url for 'pilot describe' command
 - Fixed 2 bugs in download command not working/displaying correctly
 - Fixed bug with login not requesting correct tokens for context
 - Fixed hardcoded nature of get_portal_url
 - Fixed up project add command to work with contexts
 - Fixed some text in docs and added types for tutorial project files
 - Fixed analyze to skip directories, can now analyze multiple files
 - Fixed bug if previous search entry was missing files metadata
 - Fixed '-u' flag being possibly needed for '--dry-run'
 - Fixed upload exit codes to return unique values for various errors
 - Fixed extended mimetype detection not working for file uploads
 - Fixed backwards compatibility for old table schema fields on text files

 - Added new docs for new client usage
 - Added new pilot.upload SDK call which automatically registers/uploads file
 - Added new pilot.register SDK call for analyzing/ingesting metadata
 - Added debugging when pliot falls back to default context
 - Added puremagic dependency for detecting mimetypes
 - Added doc to show how to call into the pilot client
 - Added debug logs to list which manifest is being pulled on update
 - Added dependency fair-research-login 0.1.5 (bumped from 0.1.1)
 - Added docs for client, fixed download, added check for ranges
 - Added 'context' switching so pilot can be used anywhere on other indices
 - Added nexus client to fetch groups on project update
 - Added parquet, feather, and h5 to pilot-tutorial. Removed extensions.
 - Added note to upload if files are > 1GB
 - Added an Analyze command separate from 'upload'
 - Added 'blind' mimetype detection without extension for several types
 - Added analysis for hdf, feather, and parquet plus tests for all.

 - Silenced normal debug errors when listing
 - Silenced Tableschema error when files have no extension

 - Removed deprecated `whoami` command
 - Removed old required fields (or fixed bug if mimetype was undetermined)

 - Renamed low level pilot.upload call to upload_globus()


### 0.3.0 - 2019-07-17

 - Fixed bug where project 'info' subcommand would not show 'public' group
 - Fixed bug in project 'edit' subcommand
 - Added script to populate pilot-tutorial, updated docs
 - Made Globus Groups dynamic
     - This changed the project manifest in a non-backwards compatible way
 - Added warning if analysis fails and propogated error info
 - Fixed pilot raising exception when listing info for nonexistent project
 - Fixed csvs not being picked up by the analyzer

### 0.2.3 - 2019-07-09


 - Added full list of user-providable dc metadata
 - Fixed bug with not being able to set home directory '~' local ep path
 - Fixed bad warning complaining about local endpoint when logging in
 - Fixed bug if login expires without a refresh token
 - Switched to prod index for storing/accessing projects
 - Fixed all edge cases with flags and when arg is a directory
 - Delete command now supports data deletion along with metadata
 - Delisted 'push' project subcommand
 - Deprecated the whoami command in favor of profile



### 0.2.2 - 2019-07-02

 -Fixed input validation validating the wrong path

### 0.2.1 - 2019-03-02

a1ac32e Small fixes
 - Made analysis a folder with the idea to support many more mimetypes
 - Changed project decorator from 'project' to 'project_command'
 - Fix when checking endpoint for the first time logging in user
 - Creating projects no longer transposes dashes to underscores

### 0.2.0 - 2019-06-28

 - Added 'pilot project delete` subcommand
 - Added mkdir command.
 - Added 'project' steps to readme
 - create user guide, make parameters distinct
 - Added 'info' command to project subcommand. 'pilot project info <x>'
 - Added interactive Add Project command with basic validation
 - Fixed upload bugs with metadata not being placed in correct places
 - Setup logging, Added warning when petrel https is down
 - More fixes, added main cli tests, streamlined client mock
 - Fixed bugs and tests, all tests now pass
 - Fixed several bugs, project subcommand should work for now



### 0.1.0 - 2019-05-21

 - Created the pilot1 tools project, first basic release allows users to upload files
