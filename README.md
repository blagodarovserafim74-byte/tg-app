# AI Agent Coder System

Проект переведён на двухпроцессную архитектуру:

- GUI Client — только интерфейс и отправка команд.
- Training Server — отдельный процесс, где живут trainer, daemon и hf_pipeline.

GUI больше не обучает внутри себя.
