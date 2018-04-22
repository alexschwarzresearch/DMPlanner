<h1 align="center">DMPlanner</h1>

<p align="center">
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-blue.svg" />
  </a>
  <a href="https://orcid.org/0000-0001-5159-8864">
    <img src="https://img.shields.io/badge/ORCiD-0000--0001--5159--8864-brightgreen.svg"/>
  </a>
</p>

DMPlanner helps you create the final version of your data management plan by extracting information from ORCiD and public repositories you used for your project.

## Author

Alexander Schwarz | [ORCiD](https://orcid.org/0000-0001-5159-8864)

## Technologies

 * Python 3.6
 * Flask
 * Docker
 * Bootstrap 4.0
 * JQuery

## Usage

The easiest way to run DMPlanner is with docker. If files from Zenodo records should be imported automatically your personal API key has to be written into the [dmplanner.config](dmplanner/dmplanner.config) file before you create the docker image.

1. The docker image can be built with: ```$ docker build -t dmplanner-image .```
2. After that the image can be started with: ```$ docker run -p 5000:5000 --name dmplanner dmplanner-image```

If everything is working DMPlanner should be running on ``` localhost:5000 ```.

## License

[MIT](LICENSE)
