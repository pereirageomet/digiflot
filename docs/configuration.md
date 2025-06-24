# Configuration

**Setting up your customized workflow**

For setting up your customized workflow there three configurations files used: `scheme.csv`, `samples.csv` and a sample-specific file, lets call it `my_sample.csv`.

The `scheme.csv` defines the stages. It always starts with the header "Stage,      Time(s),    Type" followed by one or more lines. Each line contains a stage name (e.g. _pH_ or _C1_), a numeric value for the time span of this stage, and the stage type, namely _Conditioning_ or _Flotation_. An example file can be found here: [scheme.csv](docs/scheme.csv)

The `samples.csv` defines the runs (or samples, respectively). It always starts with the header "Samples,Executed" followed by one or more lines. Each line contains a name for the run (e.g. `myProject-genericSample-777` or `CoSiFlot-Scree-001`), and the has-been-executed-flag, namely _Y_ and _N_ (for Yes and No). An example file can be found here: [samples.csv](docs/samples.csv)

Finally, a specific run csv file (with a name of a run defined in the `samples.csv`) needs to be provided, e.g. `CoSiFlot-Scree-001.csv`, for each run defined in `samples.csv`. The purpose of these specific run csv files is to define the process parameters for each stage. For this reason every run csv file starts with "Air flow rate,  Rotor speed,    Target pH,  Reagent,        Concentration,  Volume, Stage" followed by a number of lines equal to the number of stages specified in the `scheme.csv` file. The air flow rate (unit l/min), the rotor speed (rpm) and the target pH have numeric values. The reagent, concentration and volume accept any string. The stage needs to exactly match the stages defined in the `scheme.csv`. An example file is given at that link: [CoSiFlot-Scree-001.csv](docs/CoSiFlot-Scree-001.csv)

**Making your very own configuration file**

When starting the Lab Assistant for the first time, it creates two `configuration.json` files. One specific for the user at `~/.local/shared/DigiFloat/configuration.json`, and another one directly inside the current working folder. The two `configuration.json` files constitute a hierarchy: The user-wide `configuration.json` acts as a default configuration, and the cwd-specific file overrides the parameters of the user-wide configuration (without changing the file's content). An example of the content of such a `configuration.json` file can be found there: [configuration.json](docs/configuration.json)

**Default configuration**

The default configuration is localized at `~/.local/shared/DigiFloat/configuration.json` and is the default configuration for every instance of the Lab Assistant software called by a specific user. By changing its content, the default configuration for every call of the Lab Assistant Software can be changed (as long a local `configuration.json` file does not override the change of the default configuration).

**Reusing configurations**

The fact that there is a project-specific configuration file residing in the project directory and yet another copy in the directory of each run means that `configuration.json` files can be reused to guarantee reproducability. 