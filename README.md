# flac2mp3
Unraid app to convert Flac files to replaygained mp3s
This is the basis for an UnRaid Docker app.

### Usage
The front-end via Unraid's Docker apps will take a url and save as a replaygain-ed mp3.
If only two files are uploaded; one being a Flac the other a Cue file defining multiple songs, flac2mp3 will attempt to split the Flac into its constituent mp3s.

A mp3s will be replaygains (track-level).

A `Download` button will allow you save the single file or zip file (multi-output).

### Config
For Unraid, point it at your Audio/Media directory to save output.

#### Unraid
- Docker -> Add Container
  - Template from `chatai` and adjust port(s) and volume mounts as needed
  - Have an image in /mnt/user/Media/pictures/avatars/icon_<name>.png
  - If using Streamlit route URL port of 8501 to an unused port on the Unraid host

#### Github
- Credentials for DockerHub
  - <repo>/settings/secrets/actions
    - DOCKER_USERNAME
    - DOCKER_PASSWORD
- setup GH Actions using the `docker-image.yml` template

### Requirements
Unraid.  But this Python file can be used via CLI with few changes.
Github to store the container image (built with Github Actions).


### References
- https://selfhosters.net/docker/templating/templating/
- https://github.com/binhex/docker-templates


