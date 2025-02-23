#!/bin/bash
SESSION="${PROJECT_NAME}dev"

tmux kill-session -t $SESSION
tmux new-session -d -s $SESSION

tmux new-window -t $SESSION:1 -n 'Server'
tmux kill-window -t $SESSION:0

tmux split-window -h
tmux split-window -v
tmux select-pane -t 0
tmux split-window -v

tmux select-pane -t 0
tmux send-keys 'pc logs minio -f' C-m

tmux select-pane -t 1
tmux send-keys 'pc logs django -f' C-m

tmux select-pane -t 2
tmux send-keys 'pc logs nextjs -f' C-m

tmux select-pane -t 3
tmux send-keys 'pc nginx logs nginx -f' C-m

tmux attach -t $SESSION

