from __future__ import annotations

import typing

from randovania.exporter import pickup_exporter
from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.exporter.pickup_exporter import GenericAcquiredMemo
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.requirements.base import Requirement
from randovania.games.factorio.data_importer import data_parser
from randovania.games.factorio.generator import recipes
from randovania.games.factorio.generator.complexity import item_is_fluid
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pickup_creator

if typing.TYPE_CHECKING:
    import factorio_randovania_mod.configuration as cfg

    from randovania.games.factorio.generator.base_patches_factory import FactorioGameSpecific


class FactorioPatchDataFactory(PatchDataFactory):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.FACTORIO

    def create_data(self) -> dict:
        memo_data = GenericAcquiredMemo()

        rl = self.game.region_list

        useless_target = PickupTarget(
            pickup_creator.create_nothing_pickup(
                self.game.resource_database,
                model_name="__randovania-layout__/graphics/icons/nothing.png",
            ),
            self.players_config.player_index,
        )

        technologies = []

        for exported in pickup_exporter.export_all_indices(
            self.patches,
            useless_target,
            rl,
            self.rng,
            self.configuration.pickup_model_style,
            self.configuration.pickup_model_data_source,
            pickup_exporter.create_pickup_exporter(memo_data, self.players_config, self.game_enum()),
            useless_target.pickup,
        ):
            node = rl.node_from_pickup_index(exported.index)
            area = rl.nodes_to_area(node)

            prerequisites = []
            for other_node, req in area.connections[node].items():
                if req == Requirement.trivial() and isinstance(other_node, PickupNode):
                    prerequisites.append(other_node.extra["tech_name"])

            technologies.append(
                {
                    "tech_name": node.extra["tech_name"],
                    "locale_name": exported.name,
                    "description": exported.description,
                    "icon": exported.model.name,
                    "icon_size": 64 if exported.model.name.startswith("__base__/graphics/icons") else 256,
                    "cost": {
                        "count": node.extra["count"],
                        "time": node.extra["time"],
                        "ingredients": list(node.extra["ingredients"]),
                    },
                    "prerequisites": prerequisites,
                    "unlocks": [
                        conditional.resources[0][0].short_name
                        for conditional in exported.conditional_resources
                        if conditional.resources
                    ],
                }
            )

        return {
            "configuration_identifier": self.description.shareable_hash,
            "layout_uuid": str(self.players_config.get_own_uuid()),
            "technologies": technologies,
            "recipes": self._create_recipe_patches(),
            "starting_tech": [
                # TODO: care about amount decently
                resource.short_name
                for resource, amount in self.patches.starting_resources().as_resource_gain()
                if amount > 0
            ],
        }

    def _create_recipe_patches(self) -> list[cfg.ConfigurationRecipesItem]:
        result = []

        game_specific: FactorioGameSpecific = self.patches.game_specific
        recipes_raw = data_parser.load_recipes_raw()

        for recipe_name, modification in game_specific["recipes"].items():
            recipe = recipes_raw[recipe_name]
            category = recipes.determine_recipe_category(
                recipe_name, recipe.get("category", "crafting"), modification["ingredients"]
            )

            result.append(
                {
                    "recipe_name": recipe_name,
                    "category": category,
                    "ingredients": [
                        {"name": item_name, "amount": amount, "type": "fluid" if item_is_fluid(item_name) else "item"}
                        for item_name, amount in modification["ingredients"].items()
                    ],
                }
            )

        return result
