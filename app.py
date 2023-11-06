from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import pymongo
from pymongo import MongoClient
import pandas as pd
from bs4 import BeautifulSoup
from bson.objectid import ObjectId
import csv
import os
import pytz

fuso_horario = pytz.timezone('America/Sao_Paulo')

cluster = MongoClient(
    "<STRING_DE_CONEXAO_BANCO>"
)

db = cluster["Treinos_inatel"]

collection_jogadores = db['Jogadores']
collection_treinos_marcados = db['Treinos marcados']
collection_treinos_realizados = db['Treinos realizados']
collection_registros = db['Registros de entradas e saídas']

app = Flask(__name__)
app.config['SECRET_KEY'] = "fer"

def writer(header, data, filename):
  with open(filename, "w", newline="") as csvfile:
    planilha = csv.writer(csvfile)
    planilha.writerow(header)
    for x in data:
      planilha.writerow(x)


@app.route('/', methods=['POST', 'GET'])
def home():
  jogador = request.form.get('name')
  matricula = request.form.get('matricula')
  nome_discord = request.form.get('discord-name')
  curso = request.form.get('curso')
  modalidade = request.form.get('modalidade')

  modalidade_lista_jogadores = request.form.get('modalidade-lista-jogadores')

  if jogador is not None and matricula is not None and nome_discord is not None and curso is not None and modalidade is not None:
    collection_jogadores.insert_one({
        "_id": matricula,
        "jogador": jogador,
        "nome_discord": nome_discord,
        "curso": curso,
        "modalidade": modalidade,
        "numero_horas_total": 0.0
    })

  jogadores = collection_jogadores.find(
      {"modalidade": "{}".format(modalidade_lista_jogadores)})

  treinos = collection_treinos_marcados.find({})

  treinos_realizados = collection_treinos_realizados.find({}).sort('criado_em', -1)

  return render_template('treinos.html',
                         jogadores=jogadores,
                         treinos=treinos,
                         treinos_realizados=treinos_realizados)


@app.route('/deletar_jogador', methods=['POST', 'GET'])
def del_jogador():
  id_jogador = request.args.get('_id')

  collection_jogadores.delete_one({'_id': id_jogador})

  return redirect('/')


@app.route('/editar_jogador', methods=['POST', 'GET'])
def edit_jogador():
  id_jogador = request.args.get('_id')
  nome_edit = request.form.get('edit-jogador')
  nome_discord_edit = request.form.get('edit-nome_discord')
  curso_edit = request.form.get('edit-curso')
  modalidade_edit = request.form.get('edit-modalidade')

  collection_jogadores.update_one({'_id': id_jogador}, {
      "$set": {
          "jogador": nome_edit,
          "nome_discord": nome_discord_edit,
          "curso": curso_edit,
          "modalidade": modalidade_edit
      }
  })

  return redirect('/')


@app.route('/adicionar_treino', methods=['POST', 'GET'])
def add_treino():
  dias_semana_treino = []
  horas_treino = []

  modalidade_treino = request.form.get('modalidade-treino')

  contador = 1
  dia_semana_treino = request.form.get('dia-semana{}'.format(contador))
  hora_treino = request.form.get('hora{}'.format(contador))

  while hora_treino is not None and dia_semana_treino is not None:
    contador += 1
    dias_semana_treino.append(dia_semana_treino)
    horas_treino.append(hora_treino)
    dia_semana_treino = request.form.get('dia-semana{}'.format(contador))
    hora_treino = request.form.get('hora{}'.format(contador))

  if modalidade_treino is not None:
    collection_treinos_marcados.insert_one({
        "modalidade_treino": modalidade_treino,
        "dias_semana_treino": dias_semana_treino,
        "horas_treino": horas_treino
    })

  return redirect('/')


@app.route('/deletar_treino', methods=['POST', 'GET'])
def del_treino():
  id_treino = request.args.get('_id')
  print(id_treino)
  collection_treinos_marcados.find_one_and_delete({'_id': ObjectId(id_treino)})

  return redirect('/')


@app.route('/encerrar_semestre', methods=['POST', 'GET'])
def delete_info():
  data_planilha = datetime.now(fuso_horario).strftime("%d_%m_%Y")
  filename = "static/Treinos_esports" + data_planilha + ".csv"
  header = ('Nome', 'Matrícula', 'Curso', 'Modalidade', 'Horas Totais')
  jogadores = collection_jogadores.find({})
  data = []
  for i in jogadores:
    nome = i['jogador']
    matricula = i['_id']
    curso = i['curso']
    modalidade = i['modalidade']
    horas = str(i['numero_horas_total'])
    tupla = (nome, matricula, curso, modalidade, horas)
    data.append(tupla)

  writer(header, data, filename)

  collection_treinos_marcados.delete_many({})
  collection_treinos_realizados.delete_many({})
  collection_registros.delete_many({})
  collection_jogadores.update_many({}, {"$set": {'numero_horas_total': 0.0}})

  return redirect(
      url_for('static', filename="Treinos_esports" + data_planilha + ".csv"))


@app.route('/gerar_planilha', methods=['POST', 'GET'])
def planilha():
  data_planilha = datetime.now(fuso_horario).strftime("%d_%m_%Y")
  filename = "static/Treinos_esports" + data_planilha + ".csv"
  header = ('Nome', 'Matrícula', 'Curso', 'Modalidade', 'Horas Totais')
  jogadores = collection_jogadores.find({})
  data = []
  for i in jogadores:
    nome = i['jogador']
    matricula = i['_id']
    curso = i['curso']
    modalidade = i['modalidade']
    horas = str(i['numero_horas_total'])
    tupla = (nome, matricula, curso, modalidade, horas)
    data.append(tupla)

  writer(header, data, filename)

  return redirect(
      url_for('static', filename="Treinos_esports" + data_planilha + ".csv"))


if __name__ == '__app__':
    app.run(debug=True)