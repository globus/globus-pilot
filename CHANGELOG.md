# Changes in Pilot1 Tools


Below are major changes for each version Release. For detailed information,
see the list of commits from the last version or use `git log`.

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


