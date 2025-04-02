O Monitor Studeo é um script em Python que utiliza Selenium para monitorar o portal Studeo da Unicesumar. Ele verifica notificações e atividades pendentes a cada hora, enviando alertas por e-mail para novas atualizações. O script roda em modo headless por padrão e exibe logs no console.
Funcionalidades

> Verificação automática de notificações e atividades a cada hora.
> Envio de e-mails com novas atualizações.
> Logs detalhados no console.
> Execução em modo headless (sem interface gráfica do navegador).

Dependências

> Python 3.8+
> Firefox
> GeckoDriver

Instale as bibliotecas Python necessárias:

> pip install python-dotenv selenium schedule

Clone o repositório:

> git clone https://github.com/seu-usuario/monitor-studeo-console.git
> cd monitor-studeo-console

Configure o arquivo .env na raiz do projeto:

> EMAIL_REMETENTE=seu-email@gmail.com
> EMAIL_DESTINATARIO=destinatario@gmail.com
> EMAIL_SENHA=sua-senha-de-app
> STUDEO_USUARIO=seu-usuario-studeo
> STUDEO_SENHA=sua-senha-studeo

> Nota: Use uma senha de aplicativo para o Gmail se a autenticação em duas etapas estiver ativa.

Execute o script:

> python monitor_studeo.py

Uso

> O script inicia após 3 segundos e verifica o Studeo a cada hora.
> Logs são exibidos no console.
> E-mails são enviados automaticamente para novas notificações ou atividades.
> Para parar, pressione Ctrl + C.

Configurações Opcionais:

> Modo Visível: Para ver o navegador:
> Comente options.add_argument("--headless").
> Descomente options.headless = False.
> Frequência: Para testar a cada 2 segundos, substitua o agendamento:

schedule.every(2).seconds.do(check_notifications_and_activities)
