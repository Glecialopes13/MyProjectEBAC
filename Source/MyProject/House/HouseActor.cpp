#include "HouseActor.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"

// -------------------------------------------------------
// DADOS DA PLANTA (Planta_Estudo_ARCHBLINDER_LIMPA.dxf)
// Coordenadas em metros, origem = (1.02, 1.92) no DXF
// -------------------------------------------------------
//
//  PLANTA SIMPLIFICADA (vista de cima, eixo Y aponta para o fundo):
//
//  X=0    X=1.65   X=4.35  X=4.50         X=8.65  X=9.10
//  |      |        |       |               |       |
//  +------+--------+-------+---------------+-------+  Y=12.35 (topo)
//  |      |      QUARTO 3  |               SUITE   |
//  |  P   |   2.70 x 3.75  |               1.6x2.95|
//  |  A   |                |  SALA / AREA   |       |
//  |  R   +--------+-------+    PRINCIPAL   +-------+  Y=7.40
//  |  E   |      QUARTO 2  |   4.35 x 7.25 | Q.4   |
//  |  D   |   2.70 x 3.00  |               | Banheiro
//  |  E   +--------+-------+               +-------+  Y=5.80
//  |      |      QUARTO 1  |               | Q.5   |
//  |  C   |   2.70 x 3.00  |               | Banheiro
//  |  O   +--------+-------+---------------+-------+  Y=1.50
//  |  R   |     CORREDOR / ENTRADA                  |
//  +------+-----------------------------------------+  Y=0.00
//
//  Rooms (coordenadas relativas, em metros):
//    Quarto 1:  X=[1.65,4.35]  Y=[0.15, 3.15]   2.70m x 3.00m
//    Quarto 2:  X=[1.65,4.35]  Y=[3.30, 6.30]   2.70m x 3.00m
//    Quarto 3:  X=[1.65,4.35]  Y=[6.45,10.20]   2.70m x 3.75m
//    Sala:      X=[4.50,8.65]  Y=[0.15, 7.40]   4.15m x 7.25m
//    Banheiro1: X=[4.50,7.09]  Y=[7.55, 8.80]   2.59m x 1.25m
//    Banheiro2: X=[4.50,7.09]  Y=[8.95,10.20]   2.59m x 1.25m
//    Suite:     X=[7.25,8.65]  Y=[7.40,10.35]   1.40m x 2.95m
//    Corredor:  X=[0.90,1.65]  Y=[0.15,10.20]   0.75m x 10.05m
// -------------------------------------------------------

// Origem no DXF: X_dxf=1.02, Y_dxf=1.92
// Conversao: X_ue = (X_dxf - 1.02) * 100
//            Y_ue = (Y_dxf - 1.92) * 100
FVector AHouseActor::PlantaParaUE5(float X_m, float Y_m, float Z_cm)
{
	// 1 metro = 100 cm em UE5
	return FVector(X_m * 100.0f, Y_m * 100.0f, Z_cm);
}

AHouseActor::AHouseActor()
{
	PrimaryActorTick.bCanEverTick = false;

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(
		TEXT("/Engine/BasicShapes/Cube"));
	if (CubeMesh.Succeeded())
	{
		MeshParede = CubeMesh.Object;
	}
}

void AHouseActor::BeginPlay()
{
	Super::BeginPlay();
}

void AHouseActor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	ConstruirCasa();
}

void AHouseActor::LimparComponentes()
{
	for (UStaticMeshComponent* Comp : ComponentesCriados)
	{
		if (Comp)
		{
			Comp->DestroyComponent();
		}
	}
	ComponentesCriados.Empty();
}

UStaticMeshComponent* AHouseActor::AdicionarParede(
	const FString& Nome,
	FVector Localizacao,
	FVector Escala,
	bool bExterno)
{
	UStaticMeshComponent* Comp = NewObject<UStaticMeshComponent>(this, *Nome);
	Comp->SetStaticMesh(MeshParede);
	Comp->SetRelativeLocation(Localizacao);
	// Cube mesh padrao do UE5 tem 100x100x100 unidades = 1m x 1m x 1m
	// Escala representa dimensoes em metros
	Comp->SetRelativeScale3D(Escala);
	Comp->RegisterComponent();
	Comp->AttachToComponent(GetRootComponent(), FAttachmentTransformRules::KeepRelativeTransform);

	if (bExterno && MaterialExterno)
	{
		Comp->SetMaterial(0, MaterialExterno);
	}
	else if (!bExterno && MaterialInterno)
	{
		Comp->SetMaterial(0, MaterialInterno);
	}

	ComponentesCriados.Add(Comp);
	return Comp;
}

UStaticMeshComponent* AHouseActor::AdicionarPiso(
	const FString& Nome,
	FVector Localizacao,
	FVector Escala)
{
	UStaticMeshComponent* Comp = NewObject<UStaticMeshComponent>(this, *Nome);
	Comp->SetStaticMesh(MeshParede);
	Comp->SetRelativeLocation(Localizacao);
	Comp->SetRelativeScale3D(Escala);
	Comp->RegisterComponent();
	Comp->AttachToComponent(GetRootComponent(), FAttachmentTransformRules::KeepRelativeTransform);

	if (MaterialPiso)
	{
		Comp->SetMaterial(0, MaterialPiso);
	}

	ComponentesCriados.Add(Comp);
	return Comp;
}

void AHouseActor::ConstruirCasa()
{
	LimparComponentes();

	if (!MeshParede) return;

	const float H  = AlturaParede;       // altura das paredes em cm
	const float EP = EspessuraParede;     // espessura em cm
	const float H2 = H * 0.5f;           // metade da altura (para centrar Z)
	const float EP2 = EP * 0.5f;

	// ------------------------------------------------------------------
	// Dimensoes da planta em metros (relativas, origem = canto interno)
	//   X: 0 = parede esquerda interna do edificio
	//   Y: 0 = parede frontal interna
	// ------------------------------------------------------------------

	// Largura total interna: 8.65m (X: 0 a 8.65)
	// Profundidade total interna: 10.35m (Y: 0 a 10.35)

	const float W = 865.0f;   // largura interna total (cm)
	const float D = 1035.0f;  // profundidade interna total (cm)

	// Posicoes X das paredes internas verticais (cm)
	const float X_Corredor    = 90.0f;   // X=1.92 - parede esquerda do corredor
	const float X_CorredorDir = 165.0f;  // X=2.67 - parede direita do corredor
	const float X_Central     = 435.0f;  // X=5.37 - parede central (esq)
	const float X_CentralDir  = 450.0f;  // X=5.52 - parede central (dir)
	const float X_DirSup      = 725.0f;  // X=8.27 - divisoria sup direita
	const float X_DirInt      = 865.0f;  // X=9.87 - parede interna direita

	// Posicoes Y das paredes horizontais (cm)
	const float Y_Fundo       = 15.0f;   // Y=2.07 - fundo da entrada / base dos quartos
	const float Y_Div1        = 315.0f;  // Y=5.07 - separacao Quarto1 / Quarto2
	const float Y_Div1b       = 330.0f;  // Y=5.22
	const float Y_Div2        = 630.0f;  // Y=8.22 - separacao Quarto2 / Quarto3
	const float Y_Div2b       = 645.0f;  // Y=8.37
	const float Y_SubA        = 740.0f;  // Y=9.32 - inicio sub-cômodos direitos
	const float Y_SubAb       = 755.0f;  // Y=9.47
	const float Y_SubMid      = 880.0f;  // Y=10.72 - divisoria banheiros
	const float Y_SubMidb     = 895.0f;  // Y=10.87
	const float Y_Teto        = 1020.0f; // Y=12.12 - teto dos quartos

	// ------------------------------------------------------------------
	// PAREDES EXTERNAS
	// Cube mesh 100x100x100 -> escala (comprimento_cm/100, espessura_cm/100, altura_cm/100)
	// ------------------------------------------------------------------

	// Parede frontal (sul) - Y=0
	AdicionarParede(TEXT("Parede_Frontal"),
		FVector(W * 0.5f, -EP2, H2),
		FVector(W / 100.0f, EP / 100.0f, H / 100.0f), true);

	// Parede de fundo (norte) - Y=D
	AdicionarParede(TEXT("Parede_Fundo"),
		FVector(W * 0.5f, D + EP2, H2),
		FVector(W / 100.0f, EP / 100.0f, H / 100.0f), true);

	// Parede esquerda (oeste) - X=0
	AdicionarParede(TEXT("Parede_Esquerda"),
		FVector(-EP2, D * 0.5f, H2),
		FVector(EP / 100.0f, (D + EP * 2.0f) / 100.0f, H / 100.0f), true);

	// Parede direita (leste) - X=W
	AdicionarParede(TEXT("Parede_Direita"),
		FVector(W + EP2, D * 0.5f, H2),
		FVector(EP / 100.0f, (D + EP * 2.0f) / 100.0f, H / 100.0f), true);

	// ------------------------------------------------------------------
	// PAREDES INTERNAS VERTICAIS (paralelas ao eixo Y)
	// ------------------------------------------------------------------

	// Parede do corredor esquerdo
	AdicionarParede(TEXT("Parede_Corredor_Esq"),
		FVector(X_Corredor, Y_Fundo + (Y_Teto - Y_Fundo) * 0.5f, H2),
		FVector(EP / 100.0f, (Y_Teto - Y_Fundo) / 100.0f, H / 100.0f));

	// Parede direita do corredor / esquerda dos quartos
	AdicionarParede(TEXT("Parede_Corredor_Dir"),
		FVector(X_CorredorDir, Y_Fundo + (Y_Teto - Y_Fundo) * 0.5f, H2),
		FVector(EP / 100.0f, (Y_Teto - Y_Fundo) / 100.0f, H / 100.0f));

	// Parede central (esquerda) - separa quartos da sala
	float AltCentralEsq = Y_Div1 - Y_Fundo;  // ate Div1 (sem abertura da porta)
	AdicionarParede(TEXT("Parede_Central_Esq_Inf"),
		FVector(X_Central, Y_Fundo + AltCentralEsq * 0.5f, H2),
		FVector(EP / 100.0f, AltCentralEsq / 100.0f, H / 100.0f));

	float AltCentralMid = Y_Div2 - Y_Div1b;
	AdicionarParede(TEXT("Parede_Central_Esq_Mid"),
		FVector(X_Central, Y_Div1b + AltCentralMid * 0.5f, H2),
		FVector(EP / 100.0f, AltCentralMid / 100.0f, H / 100.0f));

	float AltCentralSup = Y_SubA - Y_Div2b;
	AdicionarParede(TEXT("Parede_Central_Esq_Sup"),
		FVector(X_Central, Y_Div2b + AltCentralSup * 0.5f, H2),
		FVector(EP / 100.0f, AltCentralSup / 100.0f, H / 100.0f));

	float AltCentralTop = Y_Teto - Y_SubAb;
	AdicionarParede(TEXT("Parede_Central_Esq_Top"),
		FVector(X_Central, Y_SubAb + AltCentralTop * 0.5f, H2),
		FVector(EP / 100.0f, AltCentralTop / 100.0f, H / 100.0f));

	// Parede central (direita) - espessura da parede
	AdicionarParede(TEXT("Parede_Central_Dir"),
		FVector(X_CentralDir, Y_Fundo + (Y_Teto - Y_Fundo) * 0.5f, H2),
		FVector(EP / 100.0f, (Y_Teto - Y_Fundo) / 100.0f, H / 100.0f));

	// Divisoria dos sub-comodos direitos (X=8.27)
	float AltDirSup = Y_Teto - Y_SubA;
	AdicionarParede(TEXT("Parede_Dir_Superior"),
		FVector(X_DirSup, Y_SubA + AltDirSup * 0.5f, H2),
		FVector(EP / 100.0f, AltDirSup / 100.0f, H / 100.0f));

	// Parede interna direita (X=9.87)
	float AltDirInt = Y_Teto - Y_Fundo;
	AdicionarParede(TEXT("Parede_Dir_Interna"),
		FVector(X_DirInt, Y_Fundo + AltDirInt * 0.5f, H2),
		FVector(EP / 100.0f, AltDirInt / 100.0f, H / 100.0f));

	// ------------------------------------------------------------------
	// PAREDES INTERNAS HORIZONTAIS (paralelas ao eixo X)
	// ------------------------------------------------------------------

	// Base dos quartos (Y=15cm) - lado esquerdo
	float LargEsq = X_Central - X_CorredorDir;
	AdicionarParede(TEXT("Parede_Base_Quartos_Esq"),
		FVector(X_CorredorDir + LargEsq * 0.5f, Y_Fundo, H2),
		FVector(LargEsq / 100.0f, EP / 100.0f, H / 100.0f));

	// Base dos quartos (Y=15cm) - lado direito (sala)
	float LargDir = X_DirInt - X_CentralDir;
	AdicionarParede(TEXT("Parede_Base_Sala"),
		FVector(X_CentralDir + LargDir * 0.5f, Y_Fundo, H2),
		FVector(LargDir / 100.0f, EP / 100.0f, H / 100.0f));

	// Divisoria Quarto1 / Quarto2 (Y=5.07)
	AdicionarParede(TEXT("Parede_Div_Q1_Q2_A"),
		FVector(X_CorredorDir + LargEsq * 0.5f, Y_Div1, H2),
		FVector(LargEsq / 100.0f, EP / 100.0f, H / 100.0f));

	AdicionarParede(TEXT("Parede_Div_Q1_Q2_B"),
		FVector(X_CorredorDir + LargEsq * 0.5f, Y_Div1b, H2),
		FVector(LargEsq / 100.0f, EP / 100.0f, H / 100.0f));

	// Divisoria Quarto2 / Quarto3 (Y=8.22)
	AdicionarParede(TEXT("Parede_Div_Q2_Q3_A"),
		FVector(X_CorredorDir + LargEsq * 0.5f, Y_Div2, H2),
		FVector(LargEsq / 100.0f, EP / 100.0f, H / 100.0f));

	AdicionarParede(TEXT("Parede_Div_Q2_Q3_B"),
		FVector(X_CorredorDir + LargEsq * 0.5f, Y_Div2b, H2),
		FVector(LargEsq / 100.0f, EP / 100.0f, H / 100.0f));

	// Teto dos quartos (Y=10.20m) - lateral esquerda
	AdicionarParede(TEXT("Parede_Teto_Quartos_Esq"),
		FVector(X_CorredorDir + LargEsq * 0.5f, Y_Teto, H2),
		FVector(LargEsq / 100.0f, EP / 100.0f, H / 100.0f));

	// Divisoria superior direita - inicio sub-comodos (Y=9.32)
	float LargSubDir = X_DirSup - X_CentralDir;
	AdicionarParede(TEXT("Parede_Sub_Inicio_A"),
		FVector(X_CentralDir + LargSubDir * 0.5f, Y_SubA, H2),
		FVector(LargSubDir / 100.0f, EP / 100.0f, H / 100.0f));

	AdicionarParede(TEXT("Parede_Sub_Inicio_B"),
		FVector(X_CentralDir + LargSubDir * 0.5f, Y_SubAb, H2),
		FVector(LargSubDir / 100.0f, EP / 100.0f, H / 100.0f));

	// Divisoria entre os dois banheiros (Y=10.72)
	AdicionarParede(TEXT("Parede_Div_Banheiros_A"),
		FVector(X_CentralDir + LargSubDir * 0.5f, Y_SubMid, H2),
		FVector(LargSubDir / 100.0f, EP / 100.0f, H / 100.0f));

	AdicionarParede(TEXT("Parede_Div_Banheiros_B"),
		FVector(X_CentralDir + LargSubDir * 0.5f, Y_SubMidb, H2),
		FVector(LargSubDir / 100.0f, EP / 100.0f, H / 100.0f));

	// Teto da sala / suite (Y=10.20m) - lado direito
	float LargDirTeto = X_DirInt - X_CentralDir;
	AdicionarParede(TEXT("Parede_Teto_Dir"),
		FVector(X_CentralDir + LargDirTeto * 0.5f, Y_Teto, H2),
		FVector(LargDirTeto / 100.0f, EP / 100.0f, H / 100.0f));

	// ------------------------------------------------------------------
	// PISO (plano horizontal, Z=-EP2)
	// ------------------------------------------------------------------
	AdicionarPiso(TEXT("Piso_Principal"),
		FVector(W * 0.5f, D * 0.5f, -EP2),
		FVector(W / 100.0f, D / 100.0f, EP / 100.0f));

	// ------------------------------------------------------------------
	// TETO
	// ------------------------------------------------------------------
	AdicionarParede(TEXT("Teto"),
		FVector(W * 0.5f, D * 0.5f, H + EP2),
		FVector(W / 100.0f, D / 100.0f, EP / 100.0f), true);

	UE_LOG(LogTemp, Log, TEXT("AHouseActor: Casa construida com %d componentes."), ComponentesCriados.Num());
}
