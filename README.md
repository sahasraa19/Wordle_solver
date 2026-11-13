# ⚡ Pokémon Wordle: Intelligent Guessing Strategies

<p align="center">
  <strong>An interactive Pokémon guessing game powered by intelligent search algorithms.</strong>
</p>

<p align="center">
  <a href="https://wordle-solver-1-c3w3.onrender.com/">
    🎮 <strong>PLAY THE LIVE APPLICATION</strong>
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python" />
  <img src="https://img.shields.io/badge/Framework-Streamlit-FF4B4B?logo=streamlit" />
  <img src="https://img.shields.io/badge/Dataset-386%20Pokémon-yellow" />
  <img src="https://img.shields.io/badge/Algorithms-4-teal" />
</p>

---

## 📌 Overview

**Pokémon Wordle: Intelligent Guessing Strategies** is an interactive guessing game inspired by Wordle. Players attempt to identify a hidden Pokémon using attribute-based clues and a maximum of **8 guesses**.

Beyond human gameplay, the project implements four AI guessing strategies and compares their performance using automated experiments.

The project explores how candidate elimination, information theory, and worst-case optimization can improve decision-making in a constrained search problem.

## ✨ Key Features

- 🎮 **Human Gameplay:** Play the guessing game manually using attribute-based feedback.
- 🤖 **AI Demonstration:** Watch intelligent algorithms solve the game automatically.
- 📊 **Algorithm Comparison:** Compare the performance of four different guessing strategies.
- 🔍 **Attribute-Based Feedback:** Receive clues based on generation, Pokémon types, height, and weight.
- 📈 **Benchmark Analysis:** Evaluate average guesses, win rates, execution time, and other performance metrics.
- 🧩 **Modular Architecture:** Separate modules for game mechanics, dataset handling, solvers, and benchmarking.

## 🕹️ Application Preview

### Human Gameplay
![Human Gameplay](human_gameplay.png)

### AI Demonstration
![AI Demonstration](ai_demonstration.png)

### Algorithm Comparison
![Algorithm Comparison](algorithm_comparison.png)

---

## 🧠 Guessing Algorithms

The project implements four strategies:

| Strategy | Approach |
|---|---|
| Random | Selects an unguessed Pokémon randomly without using feedback to optimize guesses. |
| Filter | Eliminates Pokémon inconsistent with previous feedback. |
| Entropy | Selects guesses using expected information gain. |
| Minimax | Minimizes the largest possible remaining candidate group. |

### 1. Random Strategy
Acts as the baseline approach. It selects guesses randomly and does not use previous clues to improve its decisions.

### 2. Filter Strategy
Maintains a set of possible Pokémon and removes candidates that do not match the feedback received from earlier guesses.

### 3. Entropy Strategy
Uses information theory to select guesses that are expected to reduce uncertainty about the hidden Pokémon.

### 4. Minimax Strategy
Evaluates possible feedback outcomes and chooses guesses that minimize the worst-case number of remaining candidates.

---

## 📂 Dataset

The project uses a dataset containing **386 Pokémon records**.

Each record contains the following attributes:

| Attribute | Description |
|---|---|
| Name | Pokémon name |
| Generation | Pokémon generation |
| Type 1 | Primary Pokémon type |
| Type 2 | Secondary Pokémon type |
| Height | Pokémon height |
| Weight | Pokémon weight |

These attributes are used to generate feedback and progressively narrow down the possible answers.

---

## 🏗️ Project Architecture

The project follows a modular Python architecture.

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

### Core Modules

| File | Responsibility |
|---|---|
| `loader.py` | Loads and prepares the Pokémon dataset. |
| `engine.py` | Handles game mechanics, guesses, and feedback generation. |
| `basic_solvers.py` | Implements Random and Filter strategies. |
| `entropy_solver.py` | Implements the Entropy-based solver. |
| `minimax_solver.py` | Implements the Minimax solver. |
| `benchmark.py` | Runs automated experiments and generates benchmark results. |
| `research_lab.py` | Supports research and algorithm experimentation. |
| `app.py` | Runs the Streamlit application. |

---

## 📊 Experimental Results

All strategies were evaluated using a maximum of **8 guesses per game**.

The experiment used different numbers of runs:

- Random: 5 runs for each of the 386 possible hidden Pokémon (1,930 runs).
- Filter: 5 runs for each of the 386 possible hidden Pokémon (1,930 runs).
- Entropy: 1 run for each hidden Pokémon (386 runs).
- Minimax: 1 run for each hidden Pokémon (386 runs).

### Performance Comparison

| Strategy | Runs | Avg. Guesses | Median | Worst Case | Win Rate | Solved ≤6 | ms/game |
|---|---:|---:|---:|---:|---:|---:|---:|
| Random | 1930 | 8.91 | 9 | 9 | 1.97% | 1.45% | 0.08 |
| Filter | 1930 | 3.67 | 4 | 9 | 99.95% | 99.12% | 0.61 |
| Entropy | 386 | **3.07** | 3 | 5 | 100% | 100% | 2.72 |
| Minimax | 386 | 3.14 | 3 | 5 | 100% | 100% | 2.29 |

**Note:** A score of 9 represents an unsuccessful game, using the project's `FAIL_SCORE` convention. The actual game limit is 8 guesses.

### Benchmark Visualization

![Benchmark Performance Comparison](benchmark_chart.png)

### Key Observations

- Random guessing performs poorly because it does not use feedback to guide decisions.
- Filter significantly improves performance through candidate elimination.
- Entropy achieves the lowest average guess count of **3.07**.
- Minimax solves all evaluated cases within five guesses.
- Filter has lower execution time than the two advanced strategies in this benchmark.

---

## 🛠️ Technologies Used

- **Python** – Core programming language.
- **Streamlit** – Interactive web application.
- **Pandas** – Dataset handling and analysis.
- **NumPy** – Numerical operations.
- **Matplotlib** – Benchmark visualization.
- **GitHub** – Version control and project collaboration.
- **Render** – Application deployment.

---

## 🚀 Run Locally

### Prerequisites

- Python 3.11 or compatible version.
- Git.
- pip.

### Installation

**1. Clone the repository**

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

**2. Navigate to the project directory**

```bash
cd pokemon_wordle
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Run the application**

```bash
streamlit run app.py
```

The application will be available at:

```text
http://localhost:8501
```

---

## 🌐 Live Deployment

The application is deployed using Render.

<p align="center">
  <a href="https://wordle-solver-1-c3w3.onrender.com/">
    <strong>⚡ Open Pokémon Wordle — Live Demo</strong>
  </a>
</p>

---

## 👥 Team Members

| Name | Student ID |
|---|---|
| Badagoni Sri Sahasra | B24DS003 |
| Malraju Srinayana | B24CS024 |
| Nagineni Thanmaie | B24EC019 |
| Parinitha Pulipati | B24CS037 |
| V. Varshitha | B24ME050 |

**Academic Year:** 2026–27

---

## 🎯 Project Objective

The primary objective is to investigate how different intelligent guessing strategies perform in a constrained attribute-based search environment.

By implementing and benchmarking Random, Filter, Entropy, and Minimax approaches, the project demonstrates the relationship between information gain, candidate reduction, computational cost, and guessing efficiency.

---

<p align="center">
  <strong>Pokémon Wordle: Intelligent Guessing Strategies</strong><br/>
  Built with Python, Streamlit, and intelligent search algorithms ⚡
</p>
