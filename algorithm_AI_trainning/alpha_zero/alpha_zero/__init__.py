#+ AlphaZero package initializer
#+
#+ This file makes the local `alpha_zero` directory a proper Python
#+ package so that imports like `from alpha_zero.envs.gomoku import GomokuEnv`
#+ work when this project is used as a library inside other codebases.
#+
#+ The original AlphaZero implementation was structured as a standalone
#+ project; this lightweight initializer enables reuse without modifying
#+ the core training code.


