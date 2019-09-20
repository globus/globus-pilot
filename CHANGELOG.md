# Changes in Pilot1 Tools


Below are major changes for each version Release. For detailed information,
see the list of commits from the last version or use `git log`.

### 0.4.1 - 2019-09-20

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


