import sqlite3
import csv

EXCHANGE_RATE_EUR = 25.0

con = sqlite3.connect('data/test.db')
cur = con.cursor()


def date_check_ok() -> bool:
    raw_sql = """
        select count(*)
        from smlouvy
        where cast(substr(platnost_do, 9, 2) as int) > 12
    """
    res = cur.execute(raw_sql)
    error_cnt = res.fetchone()[0]

    return True if error_cnt == 0 else False


def fix_date() -> str:
    if date_check_ok():
        raw_sql = """
            update smlouvy
            set platnost_do = substr(platnost_do, 1, 4) || '-' || substr(platnost_do, 9, 2) || '-' || substr(platnost_do, 6, 2)
        """
        cur.execute(raw_sql)
        con.commit()
        fix_date_result = 'OK'
    else:
        fix_date_result = 'NOK, one or more months is greater than 12'

    return fix_date_result


def gwh_cons_by_date_and_id(contract_id: int, date_from: str, date_to: str) -> float:
    raw_sql = """
        select sum(spotreba_mwh)
        from spotreba
        where id_smlouvy = ?
              and date(dates) between date(?) and date(?)
    """
    gwh_cons = cur.execute(raw_sql, [contract_id, date_from, date_to]).fetchone()[0]

    with open('data/task2_result.csv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Contract_ID', 'Date From', 'Date To', 'GWH Cons'])
        writer.writerow([contract_id, date_from, date_to, gwh_cons])

    return gwh_cons


def total_cons_table(exchange_rate_eur: float, date_from: str, date_to: str) -> str:
    create_tab = """
        create table if not exists celkova_spotreba ("id_smlouvy" INTEGER, "spotreba_mwh_czk" REAL)
    """
    cur.execute(create_tab)

    truncate_tab = """
        delete from celkova_spotreba
    """
    cur.execute(truncate_tab)

    insert_data = """
        insert into celkova_spotreba
        select sm.id as id_smlouvy,
               sum(sp.spotreba_mwh * sm.cena_za_mwh * case mena when 'EUR' then ? else 1 end) as spotreba_mwh_czk
        from spotreba sp
              join smlouvy sm on sp.id_smlouvy = sm.id
        where date(dates) between date(?) and date(?)
        group by sm.id
        order by sm.id
    """
    cur.execute(insert_data, [exchange_rate_eur, date_from, date_to])
    con.commit()

    return 'OK'


task_one_state = fix_date()
print(f'Task 1: {task_one_state}')

gwh_sum = gwh_cons_by_date_and_id(contract_id=1234, date_from='2022-06-01', date_to='2022-06-30')
print(f'Task 2: {gwh_sum}')

insert_res = total_cons_table(exchange_rate_eur=EXCHANGE_RATE_EUR, date_from='2022-01-01', date_to='2022-12-31')
print(f'Task 3: {insert_res}')
