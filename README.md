# POKEMON_WORDLE_SOLVER

A Streamlit-based Pokémon guessing game implementing four intelligent guessing strategies: Random, Filter, Entropy, and Minimax.

## Live Demo

[🎮 Play Pokémon Wordle](https://wordle-solver-1-c3w3.onrender.com/)

An interactive Pokémon Wordle game that explores and compares intelligent guessing strategies. The project combines a Pokémon dataset, a Wordle-style feedback engine, automated solvers, benchmarking, and a Streamlit-based application.

## Project Overview

The objective of this project is to develop a Pokémon guessing game and investigate how different algorithms can identify a hidden Pokémon using attribute-based clues.

**Dataset:** 386 Pokémon records  
**Attributes:** Name, Generation, Type 1, Type 2, Height, Weight  
**Maximum guesses:** 8  
**Strategies:** Random, Filter, Entropy, Minimax  
**Interface:** Streamlit

## Features

- Interactive Pokémon guessing game.
- Attribute-based feedback after each guess.
- Automated Pokémon guessing using four algorithms.
- AI demonstration and algorithm comparison.
- Benchmark statistics and visualizations.
- Dataset exploration and research analytics.

## Guessing Strategies

| Strategy | Description |
|---|---|
| Random | Selects a Pokémon randomly from the available candidates. |
| Filter | Eliminates candidates that do not match the feedback from previous guesses. |
| Entropy | Selects guesses based on expected information gain to reduce uncertainty. |
| Minimax | Selects guesses to minimize the largest possible remaining candidate group. |

All strategies operate under the maximum limit of eight guesses.

## Dataset

The dataset contains 386 Pokémon records with the following attributes:

- Pokémon name
- Generation
- Primary type
- Secondary type
- Height
- Weight

The dataset is stored in the `data/` directory.

## Application Modes

1. **Human Gameplay:** Allows users to play Pokémon Wordle themselves.
2. **AI Demonstration:** Demonstrates how an automated strategy solves the game.
3. **Algorithm Comparison:** Compares the performance of the four guessing strategies.

The upgraded research interface also provides analytics and dataset exploration views.

## Benchmark Methodology

The strategies were evaluated using the 386 possible hidden Pokémon.

| Strategy | Runs |
|---|---:|
| Random | 1,930 |
| Filter | 1,930 |
| Entropy | 386 |
| Minimax | 386 |

Random and Filter were tested five times for every hidden Pokémon. Entropy and Minimax were tested once for every hidden Pokémon.

All experiments used the same maximum of eight guesses. The saved benchmark results are available in `results/results_table.csv`.

To regenerate the benchmark results, run:

```bash
python benchmark.py
```

## Technologies Used

- Python
- Streamlit
- Pandas
- NumPy
- Matplotlib

Refer to `requirements.txt` for the complete dependency list.

## Project Structure

```text
pokemon_wordle/
│
├── data/
│   ├── pokemon.csv
│   ├── pokemon_full.csv
│   └── pokemon_sample_backup.csv
│
├── results/
│   ├── results_table.csv
│   └── benchmark_chart.png
│
├── notebooks/
│   ├── main.ipynb
│   ├── basic_solvers.ipynb
│   ├── mem1.ipynb
│   ├── mem3.ipynb
│   └── mem4.ipynb
│
├── slides/
│   ├── project_presentation.pdf
│   └── project_presentation.pptx
│
├── loader.py
├── engine.py
├── basic_solvers.py
├── entropy_solver.py
├── minimax_solver.py
├── benchmark.py
├── research_lab.py
├── app.py
├── requirements.txt
└── README.md
```



## Installation and Execution

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd <YOUR_PROJECT_FOLDER>
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

**Windows:**

```bash
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

For the research interface:

```bash
streamlit run research_lab.py
```

If your final project uses `app.py` as its main interface, use:

```bash
streamlit run app.py
```

Open the local URL displayed in the terminal.

## Team Members

This project was collaboratively developed by:

| No. | Name | Student ID | Contribution |
|---|---|---|---|
| 1 | Badagoni Sri Sahasra | B24DS003 | Application integration and final project report |
| 2 | Malraju Srinayana | B24CS024 | Data preparation and game engine |
| 3 | Nagineni Thanmaie | B24EC019 | Random and Filter strategies |
| 4 | Parinitha Pulipati | B24CS037 | Entropy strategy |
| 5 | V. Varshitha | B24ME050 | Minimax strategy and benchmarking |


### Human Gameplay

<img src="https://github.com/user-attachments/assets/25c095cc-10ba-4a3b-a122-f6f531411e93" width="800" />

## Conclusion

Pokémon Wordle demonstrates how different intelligent guessing strategies can be applied to a constraint-based guessing game. By implementing and comparing Random, Filter, Entropy, and Minimax approaches, the project provides an interactive way to understand candidate elimination, information gain, and worst-case optimization.

