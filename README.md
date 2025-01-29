1. Есть простой сервер с двумя ендпоинтами (создать и смотреть сущность "отзыв")
2. При создании сущностей отправляется сообщение в топик, топик читает косньюмер и обрабатывает.
   Обработка сводится к печати сообщений в лог
3. Сущности хранятся в postgresql
4. Все обернуто в докер, можно поднять на `docker compose up --build`
5. С сервера собираются метрики (grafana + prometheus)
6. Весь код покрыт тестами, покрытие **почти** 100% (~95%) (это строчки кода, которые нецелесообразно проверять в тестах, подробнее [тут](https://github.com/bulatovv/hse-python-proj/actions/runs/13026727478/job/36337047541)
7. Тесты автоматизированы через github actions на каждый пулл реквест 
