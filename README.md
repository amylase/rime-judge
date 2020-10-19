# Rime Judge

A simple web-based contest system for programming contest organizers to host a mock contest.


## Warning / 警告

日本語の警告は英語に続きます (Japanese warning follows after English one.)

This software is designed for the private mock contest to evaluate contest problems. 
All submitted codes are trusted and executed without any conditions.
Therefore, anyone can run any code remotely if you expose the system on public internet.

このシステムはプログラミングコンテストの出題者が問題を評価する目的で実施する非公開コンテストのために設計されています。提出されるコードは無条件に信頼され、実行されます。
したがって、このシステムが一般のインターネットに公開された場合、実行しているコンピュータは任意の人間に任意のコードを実行される危険性があります。


## Installation

```shell script
pip install -r requirements.txt
```

## Usage

Add `contest.json` file to the top of the Rime project directory you want to use with the following content.
```json
{
  "n_workers": 1,
  "start_time": "2020-10-01T12:00:00",
  "end_time": "2020-10-01T15:00:00"
}
```
* n_workers: Judge concurrency level.
* start_time, end_time: Contest duration.

```shell script
CONTEST_PROJECT=<path to Rime project directory> python app.py
```

You can test your installation by using `example` project.
```shell script
CONTEST_PROJECT=example python app.py
```


## Contest Operation

The system generates `contest_cache` directory under the project to persist contest status.
You can restart the server if you preserve this directory, or reset the contest status by removing it.


## License

- The content under `example` directory, except for `contest.json`, is licensed by Rime Project under MIT License.
- The other files are licensed by Shunsuke Ohashi (amylase) under MIT License.