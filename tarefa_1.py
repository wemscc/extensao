import tkinter.messagebox
from tkinter import ttk

from display_treatment import *
from tkinter import *  # importando o Tkinter
from PIL import ImageTk, Image

"""
def search():
    value_to_search = var.get()
    if value_to_search == "" or value_to_search == " ":
        dim_combo['values'] = element_names
    else:
        value_to_siplay = []
        for value in element_names:
            if value_to_search in value:
                value_to_siplay.append(value)
        dim_combo['values'] = value_to_siplay
"""

# Classes de resistência de madeira
woods_class = ['C14', 'C16', 'C18', 'C20', 'D18', 'D24']

# Cria a variável utilizada para criar a janela
window = Tk()
teste()
teste2()


# Função I - O objetivo dessa função na verdade é mais para teste; Eu queria saber como pegar as informações da
# janela/abrir pop-ups/etc. Eu também quis criar ela porque eu imagino que tenham algumas condições de existência no
# nosso problema, tipo, "a largura não pode ser três vezes ou maior que a altura" (exemplo hipotético),
# mas como não consegui imaginar nada (não sei engenharia de edificações o suficiente ainda),
# resolvi deixar só essa condição lógica de que a medida deve ser não nula/não negativa
def confirm_dim():
    a = float(a_entry.get())
    b = float(b_entry.get())
    if a <= 0 or b <= 0:
        tkinter.messagebox.showwarning(title="Erro", message="Medidas inválidas. Por favor tente novamente.")
    else:
        msg = f'Classe de resistência {wood_var.get()} com medidas:\na = {a}\nb = {b}'
        tkinter.messagebox.showinfo(title="Sucesso", message=msg)
    print(unityVar.get())


# Atribui o nome dessa janela
window.title("Tarefa I")

# Pega as dimensões do monitor
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

# Define a resolução da janela de forma que a mesma tenha um mesmo tamanho proporcional em qualquer tela
window_resolution = str(int(screen_width / (3 / 2))) + 'x' + str(int(screen_height / 3))

# Cria a janela
window.geometry(window_resolution)

# Carrega a imagem que contém a imagem que indica o que cada variável significa
# img = ImageTk.PhotoImage(Image.open("tarefa_1.png"))
img_um = Image.open("thumbnail.png")
img_um = img_um.resize((280, 205))
img = ImageTk.PhotoImage(img_um)

# Cria o frame principal
frame = Frame(window)
frame.pack()

# Cria os outros dois frames
dimensions_frame = LabelFrame(frame, text="Dimensões", labelanchor="n")
imagem_widget = Label(frame, image=img)

# Inserindo a posição da imagem
imagem_widget.grid(row=0, column=0,padx=50)

# Criando o label os campos onde o usuário digita as dimensões das variáveis a e b.
dimensions_frame = LabelFrame(frame, text="Dimensões", labelanchor="n", padx=50)

# Definindo a posição desse label
dimensions_frame.grid(row=0, column=1)

# Criando os labels e a entrybox relativos a variável a
valueofA_label = Label(dimensions_frame, text="Valor de 'a'")
valueofA_label.grid(row=0, column=1)
a_entry = Entry(dimensions_frame)
a_entry.insert(0, 0)
a_entry.grid(row=1, column=1)

# Criando os labels e a entrybox relativos a variável b
valueofB_label = Label(dimensions_frame, text="Valor de 'b'")
valueofB_label.grid(row=2, column=1)
b_entry = Entry(dimensions_frame)
b_entry.insert(0, 0)
b_entry.grid(row=3, column=1)

# Radiobuttons das unidades de medidas;
unityVar = IntVar(value=1)
rb_unity = Radiobutton(dimensions_frame, text="Metros (m)", variable=unityVar, value=1)
rb_unity.grid(row=1, column=3, sticky='w', padx=10)
rb2_unity = Radiobutton(dimensions_frame, text="Centímetros (cm)", variable=unityVar, value=2)
rb2_unity.grid(row=2, column=3, sticky='w', padx=10)
rb3_unity = Radiobutton(dimensions_frame, text="Milímetros (mm)  ", variable=unityVar, value=3)
rb3_unity.grid(row=3, column=3, sticky='w', padx=10)

# Dropdown dos tipos/classes de madeira
wood_var = StringVar()
wood_var.set(woods_class[0])
woods_label = tkinter.Label(dimensions_frame, text="Classe de resistência")
woods_label.grid(row=0, column=0, sticky='w', padx=10)
woods_drop = OptionMenu(dimensions_frame,wood_var, *woods_class)
woods_drop.grid(row=1, column=0, sticky='s', padx=10)
woods_combobox = ttk.Combobox(dimensions_frame, values=woods_class)
woods_combobox.grid(row=2,column=0,padx=10)

# Botão de confirmação
confirm_button = Button(dimensions_frame, text="Confirmar", command=confirm_dim)
confirm_button.grid(row=4, column=1, pady=10)

window.mainloop()
