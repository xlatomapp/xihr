# xihr


<p align="center">
<a href="https://pypi.python.org/pypi/xihr">
    <img src="https://img.shields.io/pypi/v/xihr.svg"
        alt = "Release Status">
</a>

<a href="https://github.com/xxxiio/xihr/actions">
    <img src="https://github.com/xxxiio/xihr/actions/workflows/main.yml/badge.svg?branch=release" alt="CI Status">
</a>

<a href="https://xxxiio.github.io/xihr/">
    <img src="https://img.shields.io/website/https/xxxiio.github.io/xihr/index.html.svg?label=docs&down_message=unavailable&up_message=available" alt="Documentation Status">
</a>

</p>


Japanese horse racing betting engine, support backtest and live bet


* Free software: MIT
* Documentation: <https://xxxiio.github.io/xihr/>


## Features

## Package layout

```text
xihr/
  __init__.py
  cli.py
  config/
    __init__.py
    settings.py
  core/
    __init__.py
    bus.py
    clock.py
    engine.py
    events.py
    registry.py
    types.py
  data/
    __init__.py
    models.py
    providers.py
    repositories.py
    transforms.py
  strategy/
    __init__.py
    base.py
    risk.py
    rules.py
  models/
    __init__.py
    base.py
    pipelines.py
  execution/
    __init__.py
    broker.py
    router.py
    slippage.py
  backtest/
    __init__.py
    analyzers.py
    metrics.py
    simulator.py
  storage/
    __init__.py
    artifacts.py
    kv.py
  monitoring/
    __init__.py
    health.py
    logging.py
```

* Normalised data model for races, horses, and payoffs validated with Pydantic and Pandera.
* Repository pattern for simulation and live data/betting environments.
* Strategy API with scheduling, historical lookup, and bet execution helpers.
* Typer CLI for running strategies and generating analytics reports.
* Built-in example strategies (naive favourite and value betting) and sample datasets.

## Examples

A runnable Jupyter notebook that demonstrates a full simulation using the sample
dataset is available at `notebooks/simulation_demo.ipynb`.

## Credits

This package was created with the [ppw](https://zillionare.github.io/python-project-wizard) tool. For more information, please visit the [project page](https://zillionare.github.io/python-project-wizard/).
