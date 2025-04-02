from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import smtplib
from email.mime.text import MIMEText
import schedule
import logging
import os

#Carrega a variavel do arquivo .env
load_dotenv()

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(_name_)

def enviar_email(mensagem):
    remetente = os.getenv("EMAIL_REMETENTE")
    destinatario = os.getenv("EMAIL_DESTINATARIO")
    senha = os.getenv("EMAIL_SENHA")
    msg = MIMEText(mensagem)
    msg['Subject'] = "Nova Notificação ou Atividade do Studeo"
    msg['From'] = remetente
    msg['To'] = destinatario
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(remetente, senha)
            server.sendmail(remetente, destinatario, msg.as_string())
        logger.info("E-mail enviado com sucesso: %s", mensagem)
    except Exception as e:
        logger.error("Erro ao enviar e-mail: %s", e)

# Configuração do navegador (Firefox)
options = Options()
options.add_argument("--headless")  # Executa o navegador em modo headless (sem interface gráfica) se quiser alterar para ver o navegador, remova a linha --headless e apague o # do options.headless = False
#options.headless = False  
logger.info("Inicializando o navegador Firefox...")
try:
    driver = webdriver.Firefox(options=options)
    logger.info("Navegador inicializado com sucesso!")
except Exception as e:
    logger.error("Erro ao inicializar o navegador: %s", e)
    raise

is_logged_in = False

def check_notifications_and_activities():
    global is_logged_in
    try:
        logger.info("Iniciando a função check_notifications_and_activities...")
        
        # Recarrega a página se já estiver logado
        if is_logged_in:
            logger.info("Recarregando a página atual...")
            try:
                driver.refresh()
                logger.info("Página recarregada com sucesso.")
                time.sleep(1)  # Pequena pausa após o refresh
            except Exception as e:
                logger.error("Erro ao recarregar a página: %s", e)

        # Realiza o login se necessário
        if not is_logged_in:
            logger.info("Acessando a página de login do Studeo...")
            driver.get("https://studeo.unicesumar.edu.br/#!/access/login")
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            logger.info("Página de login carregada com sucesso!")

            # Preenche o campo de usuário
            username_field = driver.find_element(By.ID, "username")
            driver.execute_script("arguments[0].value = '';", username_field)
            username_field.send_keys(os.getenv("STUDEO_USUARIO"))
            driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", username_field)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", username_field)

            # Preenche o campo de senha
            password_field = driver.find_element(By.ID, "password")
            driver.execute_script("arguments[0].value = '';", password_field)
            password_field.send_keys(os.getenv("STUDEO_SENHA"))
            driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", password_field)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", password_field)

            time.sleep(1)
            logger.info("Clicando no botão 'Entrar'...")
            entrar_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Entrar')]"))
            )
            driver.execute_script("arguments[0].click();", entrar_btn)

            # Aguarda redirecionamento para a página inicial
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'dropdown') and .//span[contains(text(), 'Notificações')]]")
                )
            )
            logger.info("Login realizado com sucesso!")
            is_logged_in = True
        else:
            logger.info("Já estamos logados, acessando a página inicial...")
            driver.get("https://studeo.unicesumar.edu.br/#!/app/home")
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'dropdown') and .//span[contains(text(), 'Notificações')]]")
                )
            )
            logger.info("Página inicial carregada com sucesso!")

        # --- Monitoramento das Notificações (Selenium somente) ---
        logger.info("Localizando e clicando no botão 'Notificações' somente via Selenium...")
        try:
            notificacoes_btn = driver.find_element(
                By.XPATH, "//div[contains(@class, 'dropdown') and .//span[contains(text(), 'Notificações')]]"
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", notificacoes_btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", notificacoes_btn)
        except Exception as e:
            logger.error("Botão 'Notificações' não encontrado via Selenium: %s", e)
            return

        time.sleep(2)  # Aguarda o modal carregar

        logger.info("Aguardando o modal de notificações...")
        modal = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'dropdown-menu') and @aria-labelledby='notification-center']")
            )
        )
        logger.info("Modal de notificações encontrado. Buscando itens...")
        notificacoes = modal.find_elements(By.XPATH, ".//div[contains(@class, 'notification-item')]")
        logger.info("Total de notificações encontradas: %d", len(notificacoes))

        novas_notificacoes = []
        for notificacao in notificacoes:
            try:
                # Adiciona 'text-complete' ao XPath para capturar notificações com esse ícone
                data_element = notificacao.find_element(
                    By.XPATH,
                    ".//span[contains(@class, 'bold') and (contains(@class, 'text-warning') or contains(@class, 'text-success') or contains(@class, 'text-complete')) and not(contains(@style, 'display: none'))]"
                )
                data = data_element.get_attribute("innerText").strip()
                try:
                    final_element = notificacao.find_element(
                        By.XPATH,
                        ".//span[contains(@ng-if, 'item.canShowFinal') and not(contains(@style, 'display: none'))]"
                    )
                    final_data = final_element.get_attribute("innerText").strip()
                    if final_data:
                        data += " " + final_data
                except Exception as e:
                    final_data = ""
                titulo_element = notificacao.find_element(By.XPATH, ".//span[contains(@class, 'toggle-more-details-title')]")
                titulo = titulo_element.get_attribute("title").strip()
                try:
                    tipo = notificacao.find_element(By.XPATH, ".//span[contains(@class, 'notification-label')]").text.strip()
                except:
                    tipo = ""
                texto_notificacao = f"Notificação: {data} - {titulo} {('- ' + tipo) if tipo else ''}"
                novas_notificacoes.append(texto_notificacao)
                logger.info("Notificação encontrada: %s", texto_notificacao)
            except Exception as e:
                logger.warning("Erro ao processar notificação: %s", e)
                continue

        try:
            with open("ultimas_notificacoes.txt", "r") as arquivo:
                ultimas_notificacoes = arquivo.read().splitlines()
        except FileNotFoundError:
            ultimas_notificacoes = []

        diferencas_notificacoes = [notif for notif in novas_notificacoes if notif not in ultimas_notificacoes]
        if diferencas_notificacoes:
            mensagem_email = "Novas notificações encontradas:\n\n" + "\n".join(diferencas_notificacoes)
            enviar_email(mensagem_email)
        else:
            logger.info("Nenhuma nova notificação detectada.")

        with open("ultimas_notificacoes.txt", "w") as arquivo:
            for notif in novas_notificacoes:
                arquivo.write(notif + "\n")

        # Fechando o dropdown de notificações enviando ESCAPE
        try:
            dropdown_parent = driver.find_element(
                By.XPATH, "//div[contains(@class, 'dropdown-menu') and @aria-labelledby='notification-center']"
            )
            class_before = dropdown_parent.get_attribute("class")
            logger.info("Dropdown antes do ESCAPE: %s", class_before)
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(1)
            class_after = dropdown_parent.get_attribute("class")
            logger.info("Dropdown após o ESCAPE: %s", class_after)
        except Exception as e:
            logger.error("Erro ao fechar o dropdown com ESCAPE: %s", e)

        # --- Monitoramento das Atividades (Selenium somente) ---
        logger.info("Localizando e clicando no botão 'Atividades' somente via Selenium...")
        try:
            atividades_elements = driver.find_elements(
                By.XPATH, "//uni-acomp-atividades//a[contains(@aria-label, 'Acompanhamento de Atividades')]"
            )
           # logger.info("Número de elementos encontrados para Atividades: %d", len(atividades_elements))
            for i, elem in enumerate(atividades_elements):
               displayed = elem.is_displayed()
           #     logger.info("Elemento %d: %s, Displayed: %s", i, elem.get_attribute("outerHTML"), displayed)
            atividades_btn = next((elem for elem in atividades_elements if elem.is_displayed()), None)
            if atividades_btn is None:
                raise Exception("Nenhum botão 'Atividades' visível encontrado.")
            driver.execute_script("arguments[0].scrollIntoView(true);", atividades_btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", atividades_btn)
        except Exception as e:
            logger.error("Botão 'Atividades' não encontrado ou não clicável via Selenium: %s", e)
            return

        time.sleep(5)  # Aguarda o modal de atividades carregar

        logger.info("Aguardando a tabela de atividades...")
        tabela_atividades = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'table')]"))
        )
        atividades = tabela_atividades.find_elements(By.XPATH, ".//tr[.//div[contains(@class, 'font-montserrat')]]")
        logger.info("Total de atividades encontradas: %d", len(atividades))

        novas_atividades = []
        for atividade in atividades:
            try:
                nome = atividade.find_element(By.XPATH, ".//div[contains(@class, 'font-montserrat')]").text.strip()
                try:
                    prazo = atividade.find_element(By.XPATH, ".//span[contains(@class, 'text-danger')]").text.strip()
                except:
                    prazo = "N/A"
                texto_atividade = f"Atividade: {nome} - {prazo}"
                novas_atividades.append({
                    'texto': texto_atividade,
                    'element': atividade
                })
                logger.info("Atividade capturada: %s", texto_atividade)
            except Exception as e:
                logger.warning("Erro ao processar atividade: %s", e)
                continue

        atividades_filtradas = []
        for atividade in novas_atividades:
            try:
                elemento = atividade['element']
                try:
                    elemento.find_element(By.XPATH, ".//span[contains(@class, 'text-primary')]")
                    logger.info("Atividade ignorada (sem pendências): %s", atividade['texto'])
                    continue
                except:
                    pass
                try:
                    elemento.find_element(By.XPATH, ".//span[contains(@class, 'text-danger')]")
                    atividades_filtradas.append(atividade['texto'])
                    logger.info("Atividade incluída (com pendências): %s", atividade['texto'])
                except:
                    logger.info("Atividade ignorada (sem prazo com text-danger): %s", atividade['texto'])
                    continue
            except Exception as e:
                logger.warning("Erro ao filtrar atividade: %s", e)
                continue

        novas_atividades_texto = atividades_filtradas

        try:
            with open("ultimas_atividades.txt", "r") as arquivo:
                ultimas_atividades = arquivo.read().splitlines()
        except FileNotFoundError:
            ultimas_atividades = []

        diferencas_atividades = [ativ for ativ in novas_atividades_texto if ativ not in ultimas_atividades]
        if diferencas_atividades:
            mensagem_email = "Novas atividades encontradas:\n\n" + "\n".join(diferencas_atividades)
            enviar_email(mensagem_email)
        else:
            logger.info("Nenhuma nova atividade detectada.")

        with open("ultimas_atividades.txt", "w") as arquivo:
            for ativ in novas_atividades_texto:
                arquivo.write(ativ + "\n")

    except Exception as e:
        logger.error("Erro durante a execução: %s", e)
        
# Execução do primeiro loop após 3 segundos
logger.info("Aguardando 3 segundos para a primeira execução...")
time.sleep(3)
check_notifications_and_activities()

# Configurando o agendamento para rodar a cada 1 hora
logger.info("Configurando o agendamento para rodar a cada 1 hora...")
schedule.every(1).hours.do(check_notifications_and_activities)
# Configurando o agendamento para rodar a cada 2 segundos
#logger.info("Configurando o agendamento para rodar a cada 2 segundos...")
#schedule.every(2).seconds.do(check_notifications_and_activities)

logger.info("Iniciando o loop principal...")
while True:
    try:
        schedule.run_pending()
        time.sleep(1)  # Sleep curto para evitar alta utilização da CPU
    except KeyboardInterrupt:
        logger.info("Script interrompido pelo usuário.")
        break
    except Exception as e:
        logger.error("Erro no loop principal: %s", e)

logger.info("Fechando o navegador...")
try:
    driver.quit()
    logger.info("Navegador fechado com sucesso.")
except Exception as e:
    logger.warning("Erro ao fechar o navegador: %s", e)