# Profiler

The profiler is a service to evaluate previously evaluated data, e.g., with respect to yielded exceptions or how long
certain parts of the evaluation took.

## Usage

Run `start_profiler.sh`.

- remote `records` endpoint of MetaLookup must be open to download the data

## Output

All output is meant to help developers. It is not refined, well documented or thoroughly tested.
Treat output as WIP and indicators only.

The output is printed directly to console and structured with `------` followed by suitable, short explanations.
