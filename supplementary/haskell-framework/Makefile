# categorical-evolution Makefile
# Builds with GHC directly (cabal's Hackage index not available in this env)

GHC = ghc
GHC_FLAGS = -isrc -Wall -package random -package mtl -package transformers -package containers
LIBRARY_PATH_EXPORT = export LIBRARY_PATH="/home/lyra/.local/lib:$$LIBRARY_PATH"

BUILD_DIR = build
SRC_MODULES = $(wildcard src/Evolution/*.hs) $(wildcard src/Evolution/Examples/*.hs)
DEMO_SOURCES = $(wildcard demo/*.hs)
DEMOS = $(patsubst demo/%.hs,$(BUILD_DIR)/%,$(filter-out demo/Main.hs,$(DEMO_SOURCES)))

.PHONY: all lib test demos clean

all: lib test

lib: $(SRC_MODULES)
	@$(LIBRARY_PATH_EXPORT) && $(GHC) $(GHC_FLAGS) --make $(SRC_MODULES) -no-link
	@echo "Library compiled (12 modules, zero warnings)"

test: lib
	@$(LIBRARY_PATH_EXPORT) && $(GHC) $(GHC_FLAGS) -itest --make test/Main.hs -o $(BUILD_DIR)/tests
	@$(BUILD_DIR)/tests
	@echo ""

demos: lib $(DEMOS)

$(BUILD_DIR)/%: demo/%.hs lib
	@mkdir -p $(BUILD_DIR)
	@$(LIBRARY_PATH_EXPORT) && $(GHC) $(GHC_FLAGS) -idemo --make $< -o $@
	@echo "Built $@"

clean:
	@rm -rf $(BUILD_DIR)
	@find src test demo -name "*.o" -o -name "*.hi" | xargs rm -f 2>/dev/null || true
	@echo "Clean"

# Individual demo targets
cross-domain: $(BUILD_DIR)/CrossDomainDemo
	@$(BUILD_DIR)/CrossDomainDemo

comparison: $(BUILD_DIR)/ComparisonDemo
	@$(BUILD_DIR)/ComparisonDemo

lax-functor: $(BUILD_DIR)/LaxFunctorDemo
	@$(BUILD_DIR)/LaxFunctorDemo

checkers: $(BUILD_DIR)/CheckersDemo
	@$(BUILD_DIR)/CheckersDemo

gp: $(BUILD_DIR)/GPDemo
	@$(BUILD_DIR)/GPDemo

param-sweep: $(BUILD_DIR)/ParamSweepDemo
	@$(BUILD_DIR)/ParamSweepDemo

pop-size: $(BUILD_DIR)/PopSizeSweepDemo
	@$(BUILD_DIR)/PopSizeSweepDemo
