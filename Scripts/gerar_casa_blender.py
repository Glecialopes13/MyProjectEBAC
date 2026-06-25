"""
Script Blender - Casa Moderna baseada na Planta DXF
Planta: Planta_Estudo_ARCHBLINDER_LIMPA.dxf

Como usar:
  1. Abra o Blender
  2. Clique na aba "Scripting" (no topo)
  3. Clique "New" -> apague o que tiver -> cole este codigo
  4. Clique no botao PLAY (triangulo) ou pressione Alt+P
"""

import bpy
import bmesh
from mathutils import Vector

# ─── CONFIGURACOES ────────────────────────────────────────────
H_PAREDE    = 2.80   # altura das paredes (m)
H_LAJE      = 0.20   # espessura das lajes (m)
EP          = 0.20   # espessura das paredes (m)
H_PEI       = 0.90   # altura do peitoril das janelas (m)
H_JANELA    = 1.50   # altura das janelas (m)
H_PORTA     = 2.10   # altura das portas (m)
# ──────────────────────────────────────────────────────────────

# ─── LIMPAR CENA ──────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for m in list(bpy.data.meshes):   bpy.data.meshes.remove(m)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)

# ─── MATERIAIS ────────────────────────────────────────────────
def mat(nome, r, g, b, metal=0.0, rough=0.8):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    n = m.node_tree.nodes["Principled BSDF"]
    n.inputs["Base Color"].default_value    = (r, g, b, 1)
    n.inputs["Metallic"].default_value      = metal
    n.inputs["Roughness"].default_value     = rough
    return m

M_ext   = mat("Reboco_Externo",  0.93, 0.91, 0.86)
M_int   = mat("Reboco_Interno",  0.98, 0.97, 0.94)
M_piso  = mat("Piso_Cimento",    0.75, 0.73, 0.68)
M_laje  = mat("Concreto_Laje",   0.85, 0.84, 0.82)
M_vidro = mat("Vidro",           0.60, 0.75, 0.85, metal=0.0, rough=0.05)
M_caixilho = mat("Caixilho_Al",  0.82, 0.82, 0.82, metal=0.9, rough=0.3)
M_piso_ext = mat("Piso_Externo", 0.65, 0.63, 0.58)

# ─── COLECOES ─────────────────────────────────────────────────
def col(nome):
    c = bpy.data.collections.new(nome)
    bpy.context.scene.collection.children.link(c)
    return c

C_ext   = col("Fachada_Paredes")
C_int   = col("Paredes_Internas")
C_lajes = col("Lajes_Pisos")
C_jan   = col("Janelas_Portas")
C_ent   = col("Entrada_Externa")

# ─── FUNCOES BASE ─────────────────────────────────────────────
def add_obj(colecao, nome, mesh, material=None):
    obj = bpy.data.objects.new(nome, mesh)
    colecao.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    return obj

def caixa(colecao, nome, x, y, z, lx, ly, lz, material=None):
    """Cria uma caixa simples."""
    me = bpy.data.meshes.new(nome)
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in [
        (x,    y,    z),    (x+lx, y,    z),
        (x+lx, y+ly, z),    (x,    y+ly, z),
        (x,    y,    z+lz), (x+lx, y,    z+lz),
        (x+lx, y+ly, z+lz), (x,    y+ly, z+lz),
    ]]
    faces = [(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    for f in faces: bm.faces.new([v[i] for i in f])
    bm.to_mesh(me); bm.free()
    return add_obj(colecao, nome, me, material)

def parede_com_abertura(colecao, nome,
                         x0, y0, z0,
                         comp, esp, h_parede,
                         aberturas,          # lista de (inicio, largura, z_ini, altura)
                         eixo='X',
                         mat_ext=None, mat_int=None):
    """
    Cria uma parede com aberturas (janelas / portas).
    eixo='X': parede se estende na direcao X (fachada sul/norte)
    eixo='Y': parede se estende na direcao Y (fachada leste/oeste)
    aberturas = [(pos_inicio_ao_longo_parede, largura, z_base, altura), ...]
    """
    # Coleta segmentos solidos ao longo do comprimento
    pontos = sorted(set([0.0, comp] +
                        [a for ab in aberturas for a in [ab[0], ab[0]+ab[1]]]))
    z_segs = [(0.0, h_parede)]  # altura total da parede

    me = bpy.data.meshes.new(nome)
    bm = bmesh.new()

    for i in range(len(pontos)-1):
        p0, p1 = pontos[i], pontos[i+1]
        centro = (p0+p1)/2.0
        # verifica se este segmento horizontal esta dentro de alguma abertura
        ab_ativas = [ab for ab in aberturas if ab[0] <= centro <= ab[0]+ab[1]-0.001]

        if not ab_ativas:
            # Segmento solido em toda a altura
            _extrudar_segmento(bm, x0, y0, z0, p0, p1, esp, 0, h_parede, eixo)
        else:
            ab = ab_ativas[0]
            z_ab_ini = ab[2]
            z_ab_fim = ab[2] + ab[3]
            # Parte abaixo da abertura (peitoril)
            if z_ab_ini > 0:
                _extrudar_segmento(bm, x0, y0, z0, p0, p1, esp, 0, z_ab_ini, eixo)
            # Parte acima da abertura (verga)
            if z_ab_fim < h_parede:
                _extrudar_segmento(bm, x0, y0, z0, p0, p1, esp, z_ab_fim, h_parede - z_ab_fim, eixo)

    bm.to_mesh(me); bm.free()
    obj = add_obj(colecao, nome, me, mat_ext)
    return obj

def _extrudar_segmento(bm, x0, y0, z0, p0, p1, esp, z_ini, alt, eixo):
    if alt <= 0 or (p1-p0) <= 0: return
    if eixo == 'X':
        verts = [
            (x0+p0, y0,     z0+z_ini),
            (x0+p1, y0,     z0+z_ini),
            (x0+p1, y0+esp, z0+z_ini),
            (x0+p0, y0+esp, z0+z_ini),
        ]
    else:
        verts = [
            (x0,     y0+p0, z0+z_ini),
            (x0+esp, y0+p0, z0+z_ini),
            (x0+esp, y0+p1, z0+z_ini),
            (x0,     y0+p1, z0+z_ini),
        ]
    base = [bm.verts.new(Vector(v)) for v in verts]
    topo = [bm.verts.new(Vector((v[0], v[1], v[2]+alt))) for v in verts]
    n = len(base)
    faces = [
        base,
        topo,
        [base[0], base[1], topo[1], topo[0]],
        [base[1], base[2], topo[2], topo[1]],
        [base[2], base[3], topo[3], topo[2]],
        [base[3], base[0], topo[0], topo[3]],
    ]
    for f in faces:
        try: bm.faces.new(f)
        except: pass

def vidro(colecao, nome, x, y, z, larg, alt, esp=0.01, eixo='X', material=None):
    """Cria um painel de vidro."""
    if eixo == 'X':
        return caixa(colecao, nome, x, y, z, larg, esp, alt, material)
    else:
        return caixa(colecao, nome, x, y, z, esp, larg, alt, material)

def caixilho(colecao, nome, x, y, z, larg, alt, esp=0.05, eixo='X', material=None):
    """Cria o caixilho (moldura) de uma janela."""
    e = 0.06  # largura do perfil
    if eixo == 'X':
        # topo, base, esquerda, direita
        caixa(colecao, nome+"_T", x, y, z+alt-e, larg, esp, e, material)
        caixa(colecao, nome+"_B", x, y, z,       larg, esp, e, material)
        caixa(colecao, nome+"_L", x, y, z,       e,    esp, alt, material)
        caixa(colecao, nome+"_R", x+larg-e, y, z, e,   esp, alt, material)
    else:
        caixa(colecao, nome+"_T", x, y, z+alt-e, esp, larg, e, material)
        caixa(colecao, nome+"_B", x, y, z,        esp, larg, e, material)
        caixa(colecao, nome+"_L", x, y, z,        esp, e,   alt, material)
        caixa(colecao, nome+"_R", x, y+larg-e, z, esp, e,   alt, material)

# ═══════════════════════════════════════════════════════════════
#  GEOMETRIA DA CASA
#  Coordenadas: X=leste, Y=norte, Z=cima
#  Origem: canto sudoeste externo da casa
#
#  Planta (interior, metros):
#    Largura  W = 8.65 m   (X: 0 a 8.65)
#    Prof     D = 10.35 m  (Y: 0 a 10.35)
# ═══════════════════════════════════════════════════════════════

W  = 8.65
D  = 10.35
H  = H_PAREDE
HL = H_LAJE

# ── 1. PISO ──────────────────────────────────────────────────
caixa(C_lajes, "Piso", -EP, -EP, -HL, W+EP*2, D+EP*2, HL, M_piso)

# ── 2. FACHADA SUL (Y=0) — janelas da sala e corredor ────────
# Sala: janela grande X=[3.60,8.65] => pos=3.60, larg=4.85
# Corredor/quarto: janelinha X=[0.75,2.50] => pos=0.75, larg=1.50
parede_com_abertura(C_ext, "Fachada_Sul",
    -EP, -EP, 0, W+EP*2, EP, H,
    aberturas=[
        (0.75+EP, 1.50, H_PEI, H_JANELA),   # janela quarto1/corredor
        (3.60+EP, 4.85, H_PEI, H_JANELA),   # janela grande sala
    ],
    eixo='X', mat_ext=M_ext)

# vidros das janelas sul
vidro(C_jan,"Vid_Sul_Q1",  0.75+EP, -EP, H_PEI,   1.50, H_JANELA, 0.01, 'X', M_vidro)
vidro(C_jan,"Vid_Sul_Sala",3.60+EP, -EP, H_PEI,   4.85, H_JANELA, 0.01, 'X', M_vidro)
caixilho(C_jan,"Cax_Sul_Q1",  0.75+EP, -EP, H_PEI,   1.50, H_JANELA, EP,'X',M_caixilho)
caixilho(C_jan,"Cax_Sul_Sala",3.60+EP, -EP, H_PEI,   4.85, H_JANELA, EP,'X',M_caixilho)

# ── 3. FACHADA NORTE (Y=D) — janelas dos quartos e suite ─────
# Quarto3: X=[0.75,3.45] => janela pos=0.75, larg=2.20
# Suite:   X=[6.35,8.65] => janela pos=6.35, larg=2.00
parede_com_abertura(C_ext, "Fachada_Norte",
    -EP, D, 0, W+EP*2, EP, H,
    aberturas=[
        (0.75+EP, 2.20, H_PEI, H_JANELA),   # quarto3
        (6.35+EP, 2.00, H_PEI, H_JANELA),   # suite
    ],
    eixo='X', mat_ext=M_ext)

vidro(C_jan,"Vid_N_Q3",   0.75+EP, D, H_PEI, 2.20, H_JANELA, 0.01,'X',M_vidro)
vidro(C_jan,"Vid_N_Suite",6.35+EP, D, H_PEI, 2.00, H_JANELA, 0.01,'X',M_vidro)
caixilho(C_jan,"Cax_N_Q3",   0.75+EP, D, H_PEI, 2.20, H_JANELA, EP,'X',M_caixilho)
caixilho(C_jan,"Cax_N_Suite",6.35+EP, D, H_PEI, 2.00, H_JANELA, EP,'X',M_caixilho)

# ── 4. FACHADA OESTE (X=0) — janelas Q1,Q2,Q3 ───────────────
parede_com_abertura(C_ext, "Fachada_Oeste",
    -EP, -EP, 0, EP, D+EP*2, H,
    aberturas=[
        (0.15+EP, 1.50, H_PEI, H_JANELA),   # quarto1
        (3.30+EP, 1.50, H_PEI, H_JANELA),   # quarto2
        (6.45+EP, 2.20, H_PEI, H_JANELA),   # quarto3
    ],
    eixo='Y', mat_ext=M_ext)

for i,(y0,larg) in enumerate([(0.15+EP,1.50),(3.30+EP,1.50),(6.45+EP,2.20)]):
    nm = f"Q{i+1}"
    vidro(C_jan,f"Vid_O_{nm}",  -EP, y0, H_PEI, larg, H_JANELA, 0.01,'Y',M_vidro)
    caixilho(C_jan,f"Cax_O_{nm}",-EP,y0, H_PEI, larg, H_JANELA,  EP, 'Y',M_caixilho)

# ── 5. FACHADA LESTE (X=W) — janelas sala / suite ────────────
parede_com_abertura(C_ext, "Fachada_Leste",
    W, -EP, 0, EP, D+EP*2, H,
    aberturas=[
        (0.15+EP, 5.00, H_PEI, H_JANELA),   # sala (grande)
        (7.40+EP, 2.00, H_PEI, H_JANELA),   # suite
    ],
    eixo='Y', mat_ext=M_ext)

vidro(C_jan,"Vid_E_Sala", W, 0.15+EP, H_PEI, 5.00, H_JANELA, 0.01,'Y',M_vidro)
vidro(C_jan,"Vid_E_Suite",W, 7.40+EP, H_PEI, 2.00, H_JANELA, 0.01,'Y',M_vidro)
caixilho(C_jan,"Cax_E_Sala", W, 0.15+EP, H_PEI, 5.00, H_JANELA, EP,'Y',M_caixilho)
caixilho(C_jan,"Cax_E_Suite",W, 7.40+EP, H_PEI, 2.00, H_JANELA, EP,'Y',M_caixilho)

# ── 6. PAREDES INTERNAS ──────────────────────────────────────
# Corredor / quartos
caixa(C_int,"Int_Corredor", 0.75,-EP,0, EP, D+EP*2, H, M_int)

# Parede central (quartos | sala) — com porta na sala (Y~0.15 a 1.00)
parede_com_abertura(C_int,"Int_Central",
    3.45, -EP, 0, EP, D+EP*2, H,
    aberturas=[(0.15+EP, 0.80, 0, H_PORTA)],   # porta corredor->sala
    eixo='Y', mat_ext=M_int)

# Divisorias horizontais dos quartos
for nome,y in [("Div_Q1Q2",3.15),("Div_Q2Q3",6.30),("Div_Q3_topo",10.20)]:
    caixa(C_int,nome, 0.75,y,0, 2.70,EP,H, M_int)

# Area banheiros / suite
caixa(C_int,"Sep_Banheiros",  3.60, 7.40, 0, 5.05, EP, H, M_int)
caixa(C_int,"Div_Ban1_Ban2",  3.60, 8.65, 0, 2.60, EP, H, M_int)
caixa(C_int,"Sep_Suite_esq",  6.35, 7.40, 0, EP, 2.95, H, M_int)

# ── 7. LAJE DO TETO (telhado plano moderno) ──────────────────
# Laje principal
caixa(C_lajes,"Teto_Principal",
    -EP, -EP, H, W+EP*2, D+EP*2, HL, M_laje)

# Viga/faixa frontal saliente (espelho de fachada)
caixa(C_lajes,"Friso_Sul",
    -EP, -EP-0.05, H-0.10, W+EP*2, 0.30, HL+0.10, M_laje)

# ── 8. ENTRADA EXTERNA ──────────────────────────────────────
# Plataforma principal
caixa(C_ent,"Plataforma",   0.50, -3.50, -HL,  5.00, 3.50, HL, M_piso_ext)

# Escada — 4 degraus
for i in range(4):
    h_deg = 0.17
    p_deg = 0.30
    caixa(C_ent, f"Degrau_{i+1}",
          1.00, -3.50 + i*p_deg, -HL + i*h_deg,
          3.00, p_deg, h_deg+(HL if i==0 else 0), M_piso_ext)

# Muro lateral da entrada
caixa(C_ent,"Muro_Ent_Dir",  5.50, -3.60, 0, EP, 3.60, 1.10, M_ext)

# ── 9. CAMERA ────────────────────────────────────────────────
bpy.ops.object.camera_add(location=(16, -12, 9))
cam = bpy.context.active_object
cam.rotation_euler = (1.05, 0.0, 0.87)
bpy.context.scene.camera = cam

# ── 10. LUZ ─────────────────────────────────────────────────
bpy.ops.object.light_add(type='SUN', location=(8, -15, 20))
sol = bpy.context.active_object
sol.data.energy  = 6
sol.data.angle   = 0.05
sol.rotation_euler = (0.65, 0.0, 0.45)

bpy.ops.object.light_add(type='AREA', location=(-5, 5, 8))
fill = bpy.context.active_object
fill.data.energy = 200
fill.data.size   = 10

# ── VIEWPORT ─────────────────────────────────────────────────
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'
        break

print("=" * 55)
print("  CASA GERADA COM SUCESSO!")
print(f"  {W:.2f}m x {D:.2f}m  |  Pe-direito: {H:.2f}m")
print("  Comodos: Corredor, 3 Quartos, Sala,")
print("           2 Banheiros, Suite")
print("  Janelas em todas as fachadas")
print("  Telhado plano com friso de fachada")
print("  Escada de entrada externa")
print("=" * 55)
print("Proximos passos:")
print("  1. Ajuste janelas/portas a gosto no editor")
print("  2. File > Export > FBX (para Unreal Engine)")
