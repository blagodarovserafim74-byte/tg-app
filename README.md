# AI Agent Coder System

Проект переведён на **двухпроцессную архитектуру**:

- **GUI Client** — только интерфейс и отправка команд.
- **Training Server** — отдельный процесс, где живут trainer/daemon/hf_pipeline.

GUI больше **не обучает внутри себя**.

## Архитектура ZeroMQ

Обмен между процессами идёт через ZeroMQ:

- **GUI -> Training Server**: команды через `REQ/REP`
- **Training Server -> GUI**: события через `PUB/SUB`

### Каналы

- Командный канал:
  - endpoint (client connect): `tcp://127.0.0.1:5555`
  - bind (server): `tcp://127.0.0.1:5555`
- Канал событий:
  - endpoint (client connect): `tcp://127.0.0.1:5556`
  - bind (server): `tcp://127.0.0.1:5556`

Настраивается через `config/config.yaml` или `.env`:

- `ZMQ_COMMAND_ENDPOINT`
- `ZMQ_EVENTS_ENDPOINT`
- `ZMQ_COMMAND_BIND`
- `ZMQ_EVENTS_BIND`
- `ZMQ_REQ_TIMEOUT_MS`

## Команды Training Server

Поддерживаются команды:

- `start_training`
- `start_auto_training`
- `stop_training`
- `resume_training`
- `get_status`
- `run_eval`
- `save_checkpoint`
- `shutdown_server`

## События от сервера в GUI

Сервер публикует топики:

- `status` — текущее состояние (`state`, `mode`, `global_step`, checkpoint, errors)
- `logs` — лог-сообщения
- `progress` — прогресс/пульсация
- `eval` — результаты оценки
- `checkpoint` — события сохранения checkpoint
- `result` — результат `start_training`/`resume_training`
- `errors` — ошибки

## Важное про потокобезопасность ZeroMQ

`PUB` сокет используется строго из **одного выделенного publisher thread**.

- Рабочие потоки сервера не пишут в сокет напрямую.
- Все события кладутся в thread-safe очередь.
- Только publisher thread читает очередь и отправляет в `PUB`.

## Запуск

Из корня проекта (Windows, рекомендуемый Python из venv):

### 1) Запуск training server

```powershell
.\.venv311\Scripts\python.exe main.py --mode training_server
```

### 2) Запуск GUI client (во втором терминале)

```powershell
.\.venv311\Scripts\python.exe main.py --mode gui
```

## Auto-training 24/7

`start_auto_training` запускает бесконечный серверный цикл:

1. сбор данных (GitHub)
2. обучение на текущем наборе
3. авто-сессия (если включена)
4. checkpoint по политике
5. повтор

Цикл живёт в `TrainingServer` + `DaemonRunner`, а не в GUI.

## Wait / Replay / Eval mode

Если новых данных нет, тренер не завершает сервис:

- уходит в `wait_mode`
- выполняет replay/eval логику
- сервер продолжает 24/7 работу

Это позволяет не останавливать систему при отсутствии свежих данных.

## Stop / Safe cancellation

`stop_training` теперь работает как реальная остановка:

- выставляется stop flag (cancellation token)
- `trainer.run_training(...)` периодически проверяет token
- manual/resume обучение завершаетcя корректно со статусом `cancelled`
- checkpoint сохраняется безопасно

## Train -> Adapter -> Inference

Теперь связка честная:

- HF pipeline экспортирует реальный PEFT adapter не только в `memory_db/training/hf_runs/.../final`, но и в `models/adapters/<adapter_name>`
- `trainer.py` больше не пишет свой служебный JSON в `adapter_config.json`, чтобы не ломать PEFT-артефакт
- `core/llm.py` загружает только валидные адаптеры (`adapter_config.json` + `adapter_model.safetensors/bin`)
- cache key LLM учитывает активный adapter, поэтому старые ответы не подменяют пост-train inference

## Checkpoint / Resume после перезапуска

Состояние обучения хранится в:

- `memory_db/training/latest_checkpoint.json`
- `memory_db/training/training_state.json`
- `memory_db/training/hf_state/runtime_state.json`

При перезапуске сервера:

- восстанавливается `global_step` и состояние
- `resume_training` может продолжить с checkpoint
- в статусе доступен `resumed_from_checkpoint`

## Схема новых файлов

- `training_service/protocol.py`
  - список валидных команд, формат ответов/событий
- `training_service/server.py`
  - ZeroMQ REP/PUB сервер
  - обработка команд
  - auto loop
  - safe stop
  - single-thread publisher
- `gui/zmq_client.py`
  - REQ клиент команд
  - SUB подписчик событий
- `gui/tabs_training.py`
  - GUI-вкладка обучения как чистый клиент сервера

## Ключевые существующие модули (переиспользуются)

- `scheduler/daemon.py` — серверный автоцикл
- `fine_tuning/trainer.py` — обучение, wait_mode, checkpoint/resume
- `fine_tuning/hf_pipeline.py` — HF train/eval/resume
- `fine_tuning/dataset_pipeline.py` — сбор датасета

Обучение не переписано с нуля, а вынесено в отдельный процесс.


## Локальные модели

Базовые локальные модели хранятся в каталоге:

```text
C:\Users\user\Documents\ai_agent_programmer_ollama_fixed\models\base
```

По вашему текущему окружению там лежат как минимум:

- `gpt-oss-20b`
- `Qwen2.5-Coder-3B-Instruct`
- `Qwen2.5-Coder-7B-Instruct`

В `LOCAL_MODEL_PATH` и `config/config.yaml -> model.local_model_path` нужно указывать не общий каталог `models\base`, а конкретную папку модели, например:

```text
C:\Users\user\Documents\ai_agent_programmer_ollama_fixed\models\base\Qwen2.5-Coder-7B-Instruct
```

## Быстрая проверка после установки

```powershell
# 1. Установка зависимостей
.\.venv311\Scripts\python.exe -m pip install -r requirements.txt

# 2. Запуск training server
.\.venv311\Scripts\python.exe main.py --mode training_server

# 3. Запуск GUI во втором окне
.\.venv311\Scripts\python.exe main.py --mode gui

# 4. Проверка web health
.\.venv311\Scripts\python.exe main.py --mode web
```

Если нужен только CLI-режим без GUI:

```powershell
.\.venv311\Scripts\python.exe main.py --mode cli --task "создай калькулятор на python"
```
