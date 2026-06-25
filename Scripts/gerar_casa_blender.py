"""
Script Blender - Gera a Casa baseada na Planta DXF
Planta: Planta_Estudo_ARCHBLINDER_LIMPA.dxf

Como usar:
  1. Abra o Blender
  2. Va em "Scripting" (aba no topo)
  3. Clique em "New" para criar novo script
  4. Cole todo este codigo
  5. Clique em "Run Script" (botao play ou Alt+P)
"""

import bpy
import bmesh

# ── CONFIGURACOES ──────────────────────────────────────────────
ALTURA_PAREDE   = 2.80   # metros
ESPESSURA       = 0.15   # metros
ALTURA_LAJE     = 0.20   # metros (laje do piso e teto)
# ───────────────────────────────────────────────────────────────

def limpar_cena():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for col in bpy.data.collections:
        bpy.data.collections.remove(col)

def criar_material(nome, r, g, b, alpha=1.0):
    mat = bpy.data.materials.get(nome)
    if mat is None:
        mat = bpy.data.materials.new(name=nome)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (r, g, b, alpha)
        bsdf.inputs['Roughness'].default_value = 0.8
    return mat

def criar_caixa(colecao, nome, x, y, z, larg, prof, alt, material=None):
    """Cria uma caixa (parede/laje) e adiciona a colecao."""
    mesh = bpy.data.meshes.new(nome + "_mesh")
    obj  = bpy.data.objects.new(nome, mesh)
    colecao.objects.link(obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    # escala para as dimensoes desejadas
    for v in bm.verts:
        v.co.x = v.co.x * larg + larg / 2 + x
        v.co.y = v.co.y * prof + prof / 2 + y
        v.co.z = v.co.z * alt  + alt  / 2 + z
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    if material:
        obj.data.materials.append(material)
    return obj

def criar_colecao(nome):
    col = bpy.data.collections.new(nome)
    bpy.context.scene.collection.children.link(col)
    return col

# ── MATERIAIS ──────────────────────────────────────────────────
limpar_cena()

mat_parede_ext  = criar_material("Parede_Externa",  0.95, 0.93, 0.88)
mat_parede_int  = criar_material("Parede_Interna",  0.98, 0.97, 0.95)
mat_piso        = criar_material("Piso",            0.85, 0.82, 0.75)
mat_laje        = criar_material("Laje_Teto",       0.92, 0.91, 0.89)
mat_garagem     = criar_material("Garagem",         0.80, 0.80, 0.80)

# ── COLECOES ───────────────────────────────────────────────────
col_ext   = criar_colecao("Paredes_Externas")
col_int   = criar_colecao("Paredes_Internas")
col_lajes = criar_colecao("Lajes")
col_extra = criar_colecao("Area_Externa")

EP = ESPESSURA
H  = ALTURA_PAREDE
HL = ALTURA_LAJE

# ═══════════════════════════════════════════════════════════════
# DIMENSOES DA PLANTA (metros, origem = canto inf-esq interior)
#
#   Largura interior: 0.0 a 8.65 m
#   Profundidade:     0.0 a 10.35 m
#
#   Comodos:
#     Corredor:   X=[0.00,0.75]  Y=[0.15,10.20]
#     Quarto 1:   X=[0.75,3.45]  Y=[0.15, 3.15]  2.70 x 3.00 m
#     Quarto 2:   X=[0.75,3.45]  Y=[3.30, 6.30]  2.70 x 3.00 m
#     Quarto 3:   X=[0.75,3.45]  Y=[6.45,10.20]  2.70 x 3.75 m
#     Sala:       X=[3.60,8.65]  Y=[0.15, 7.40]  5.05 x 7.25 m
#     Banheiro 1: X=[3.60,6.20]  Y=[7.40, 8.65]  2.60 x 1.25 m
#     Banheiro 2: X=[3.60,6.20]  Y=[8.80,10.20]  2.60 x 1.40 m
#     Suite:      X=[6.35,8.65]  Y=[7.40,10.35]  2.30 x 2.95 m
# ═══════════════════════════════════════════════════════════════

# ── PAREDES EXTERNAS ───────────────────────────────────────────

W = 8.65   # largura total interior
D = 10.35  # profundidade total interior

# Parede frontal (sul)
criar_caixa(col_ext, "Ext_Sul",    0,      -EP,  0, W,       EP, H, mat_parede_ext)
# Parede de fundo (norte)
criar_caixa(col_ext, "Ext_Norte",  0,       D,   0, W,       EP, H, mat_parede_ext)
# Parede esquerda (oeste)
criar_caixa(col_ext, "Ext_Oeste", -EP,     -EP,  0, EP, D + EP*2, H, mat_parede_ext)
# Parede direita (leste)
criar_caixa(col_ext, "Ext_Leste",  W,      -EP,  0, EP, D + EP*2, H, mat_parede_ext)

# ── PAREDES INTERNAS VERTICAIS (paralelas ao Y) ────────────────

# Parede esquerda do corredor (X=0.00 ja e a parede externa)
# Parede direita do corredor / esquerda dos quartos (X=0.75)
criar_caixa(col_int, "Int_Corredor_Dir",
    0.75, 0.15, 0, EP, 10.05, H, mat_parede_int)

# Parede central - separa quartos da sala (X=3.45 a X=3.60)
# Segmento inferior (Quarto1 - Sala): Y=0.15 a 3.15
criar_caixa(col_int, "Int_Central_Inf",
    3.45, 0.15, 0, EP, 3.00, H, mat_parede_int)
# Segmento medio (Quarto2 - Sala): Y=3.30 a 6.30
criar_caixa(col_int, "Int_Central_Mid",
    3.45, 3.30, 0, EP, 3.00, H, mat_parede_int)
# Segmento superior (Quarto3 - area dir): Y=6.45 a 10.20
criar_caixa(col_int, "Int_Central_Sup",
    3.45, 6.45, 0, EP, 3.75, H, mat_parede_int)

# Divisoria dos banheiros e suite (X=6.35)
criar_caixa(col_int, "Int_Suite_Esq",
    6.35, 7.40, 0, EP, 2.95, H, mat_parede_int)

# Parede interna direita (X=8.65 e a externa)

# ── PAREDES INTERNAS HORIZONTAIS (paralelas ao X) ──────────────

# Base dos quartos / fundo da entrada (Y=0.15)
criar_caixa(col_int, "Int_Base_Quartos",
    0.75, 0.15, 0, 2.70, EP, H, mat_parede_int)
criar_caixa(col_int, "Int_Base_Sala",
    3.60, 0.15, 0, 5.05, EP, H, mat_parede_int)

# Separacao Quarto1 / Quarto2 (Y=3.15 e Y=3.30)
criar_caixa(col_int, "Int_Div_Q1Q2_A",
    0.75, 3.15, 0, 2.70, EP, H, mat_parede_int)
criar_caixa(col_int, "Int_Div_Q1Q2_B",
    0.75, 3.30, 0, 2.70, EP, H, mat_parede_int)

# Separacao Quarto2 / Quarto3 (Y=6.30 e Y=6.45)
criar_caixa(col_int, "Int_Div_Q2Q3_A",
    0.75, 6.30, 0, 2.70, EP, H, mat_parede_int)
criar_caixa(col_int, "Int_Div_Q2Q3_B",
    0.75, 6.45, 0, 2.70, EP, H, mat_parede_int)

# Teto dos quartos (Y=10.20)
criar_caixa(col_int, "Int_Teto_Quartos",
    0.75, 10.20, 0, 2.70, EP, H, mat_parede_int)

# Inicio area banheiros/suite (Y=7.40)
criar_caixa(col_int, "Int_Sep_Banheiros",
    3.60, 7.40, 0, 5.05, EP, H, mat_parede_int)

# Separacao Banheiro1 / Banheiro2 (Y=8.65 e Y=8.80)
criar_caixa(col_int, "Int_Div_Ban_A",
    3.60, 8.65, 0, 2.60, EP, H, mat_parede_int)
criar_caixa(col_int, "Int_Div_Ban_B",
    3.60, 8.80, 0, 2.60, EP, H, mat_parede_int)

# Teto dos banheiros / suite (Y=10.35)
criar_caixa(col_int, "Int_Teto_Dir",
    3.60, 10.20, 0, 5.05, EP, H, mat_parede_int)

# ── LAJE DO PISO ───────────────────────────────────────────────
criar_caixa(col_lajes, "Piso_Principal",
    -EP, -EP, -HL, W + EP*2, D + EP*2, HL, mat_piso)

# ── LAJE DO TETO (telhado plano - estilo moderno) ──────────────
criar_caixa(col_lajes, "Teto_Principal",
    -EP, -EP, H, W + EP*2, D + EP*2, HL, mat_laje)

# Laje saliente frontal (varanda / marquise)
criar_caixa(col_lajes, "Marquise_Frontal",
    -EP, -2.50, H - 0.10, W + EP*2, 2.50, 0.20, mat_laje)

# ── AREA EXTERNA FRONTAL (entrada / garagem) ───────────────────
# Plataforma de entrada (escada/rampa)
criar_caixa(col_extra, "Plataforma_Entrada",
    0.50, -3.50, -HL, 4.00, 3.50, HL, mat_garagem)

# Degraus de acesso
for i in range(3):
    h_degrau = 0.17
    criar_caixa(col_extra, f"Degrau_{i+1}",
        1.00, -3.50 + i * 0.30, -HL + i * h_degrau,
        3.00, 0.30, h_degrau, mat_garagem)

# ── POSICIONAR CAMERA ──────────────────────────────────────────
bpy.ops.object.camera_add(location=(18, -12, 10))
cam = bpy.context.active_object
cam.rotation_euler = (1.1, 0, 0.9)
bpy.context.scene.camera = cam

# ── ADICIONAR LUZ ─────────────────────────────────────────────
bpy.ops.object.light_add(type='SUN', location=(5, -10, 15))
sol = bpy.context.active_object
sol.data.energy = 5
sol.rotation_euler = (0.7, 0.0, 0.5)

print("=" * 50)
print("CASA GERADA COM SUCESSO!")
print(f"  Largura:       {W:.2f} m")
print(f"  Profundidade:  {D:.2f} m")
print(f"  Altura parede: {H:.2f} m")
print(f"  Comodos: Corredor, 3 Quartos, Sala,")
print(f"           2 Banheiros, Suite")
print("=" * 50)
print("Proximos passos:")
print("  1. Adicione janelas e portas")
print("  2. File > Export > FBX")
print("  3. Importe no Unreal Engine")
