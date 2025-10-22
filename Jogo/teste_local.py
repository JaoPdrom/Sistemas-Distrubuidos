from motor_jogo import MotorJogo

# Cria o jogo e carrega a história
jogo = MotorJogo("historia.yaml")
jogo.iniciar_jogo()

print(jogo.obter_trecho_atual())

# -------------------------------
# CENÁRIO 1 — SEM EMPATE
# -------------------------------
print("\n=== CENÁRIO 1 — SEM EMPATE ===")

# 3 jogadores votam (2 votam na mesma opção)
jogo.registrar_voto("João", 1)
jogo.registrar_voto("Maria", 2)
jogo.registrar_voto("Pedro", 1)

resultado = jogo.calcular_resultados()
print(resultado)  # Deve avançar de trecho normalmente

print(jogo.obter_trecho_atual())  # Mostra o novo trecho


# -------------------------------
# CENÁRIO 2 — COM EMPATE
# -------------------------------
print("\n=== CENÁRIO 2 — COM EMPATE ===")

# Reinicia o jogo do começo
jogo.iniciar_jogo()
print(jogo.obter_trecho_atual())

# 4 jogadores empatam entre as opções 1 e 2
jogo.registrar_voto("João", 1)
jogo.registrar_voto("Maria", 2)
jogo.registrar_voto("Pedro", 1)
jogo.registrar_voto("Ana", 2)

resultado = jogo.calcular_resultados()
print(resultado)  # Deve detectar o empate

print(jogo.obter_trecho_atual())  # Deve mostrar apenas as opções empatadas

# Segunda votação (apenas entre as empatadas)
print("\n🔁 Segunda votação de desempate:")
jogo.registrar_voto("João", 2)
jogo.registrar_voto("Maria", 2)
jogo.registrar_voto("Pedro", 1)
jogo.registrar_voto("Ana", 2)

resultado = jogo.calcular_resultados()
print(resultado)  # Agora deve avançar pro próximo trecho

print(jogo.obter_trecho_atual())  # Mostra o novo trecho após o desempate

# -------------------------------
# CENÁRIO 3 — VOTOS INVÁLIDOS
# -------------------------------
print("\n=== CENÁRIO 3 — VOTOS INVÁLIDOS ===")

# Reinicia o jogo
jogo.iniciar_jogo()
print(jogo.obter_trecho_atual())

# Jogadores tentam votar em opções que não existem
print(jogo.registrar_voto("João", 0))  # opção 0 -> inválida
print(jogo.registrar_voto("Maria", 5))  # opção 5 -> fora do limite
print(jogo.registrar_voto("Pedro", -1)) # opção negativa -> inválida

# Jogador vota corretamente depois
print(jogo.registrar_voto("Ana", 1))

# Calcula resultados para garantir que só o voto válido contou
resultado = jogo.calcular_resultados()
print(resultado)
print(jogo.obter_trecho_atual())

# -------------------------------
# CENÁRIO 4 — CHAT LOCAL
# -------------------------------
print("\n=== CENÁRIO 4 — CHAT LOCAL ===")

jogo.enviar_mensagem_chat("João", "Alguém já jogou isso antes?")
jogo.enviar_mensagem_chat("Maria", "Acho que devemos seguir pela trilha.")
jogo.enviar_mensagem_chat("Pedro", "Concordo!")
jogo.enviar_mensagem_chat("Ana", "Vamos nessa então!")

print(jogo.obter_chat())  # formato bonito

# Também dá pra pegar o chat como lista:
print("\nLista bruta do chat:", jogo.obter_chat(formatado=False))
