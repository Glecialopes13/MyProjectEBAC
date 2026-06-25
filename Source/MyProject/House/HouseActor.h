#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "HouseActor.generated.h"

// Representa um segmento de parede: ponto inicial, final, espessura e altura
USTRUCT(BlueprintType)
struct FWallSegment
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FVector2D Start = FVector2D::ZeroVector; // cm, plano XY

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FVector2D End = FVector2D::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Thickness = 15.0f; // cm

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Height = 280.0f; // cm
};

UCLASS()
class MYPROJECT_API AHouseActor : public AActor
{
	GENERATED_BODY()

public:
	AHouseActor();

	// Altura padrao das paredes (cm)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Casa")
	float AlturaParede = 280.0f;

	// Espessura padrao das paredes externas (cm)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Casa")
	float EspessuraParede = 15.0f;

	// Mesh usado em cada segmento de parede (default: Engine Cube)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Casa")
	UStaticMesh* MeshParede;

	// Material aplicado nas paredes externas
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Casa")
	UMaterialInterface* MaterialExterno;

	// Material aplicado nas paredes internas
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Casa")
	UMaterialInterface* MaterialInterno;

	// Material do piso
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Casa")
	UMaterialInterface* MaterialPiso;

	// Regenera a casa no editor ao alterar propriedades
	virtual void OnConstruction(const FTransform& Transform) override;

protected:
	virtual void BeginPlay() override;

private:
	void ConstruirCasa();
	void LimparComponentes();

	UStaticMeshComponent* AdicionarParede(
		const FString& Nome,
		FVector Localizacao,
		FVector Escala,
		bool bExterno = false);

	UStaticMeshComponent* AdicionarPiso(
		const FString& Nome,
		FVector Localizacao,
		FVector Escala);

	// Converte coordenadas da planta (metros) para UE5 (cm)
	// Origem da planta: canto inferior esquerdo da area interna
	static FVector PlantaParaUE5(float X_m, float Y_m, float Z_cm = 0.0f);

	TArray<UStaticMeshComponent*> ComponentesCriados;
};
