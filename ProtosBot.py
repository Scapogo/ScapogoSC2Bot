import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, GATEWAY, \
    CYBERNETICSCORE, STALKER, FORGE, PROTOSSGROUNDWEAPONSLEVEL1, PROTOSSGROUNDWEAPONSLEVEL2, \
    PROTOSSGROUNDARMORSLEVEL1, PROTOSSGROUNDARMORSLEVEL2, FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1, \
    STARGATE, VOIDRAY, ROBOTICSFACILITY, TWILIGHTCOUNCIL
import random


class ScapogoBot(sc2.BotAI):
    async def on_step(self, iteration):
        # what to do every step
        await self.distribute_workers()  # in sc2/bot_ai.py
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators()
        await self.expand()
        await self.offensive_force_buildings()
        await self.build_offensive_force()
        await self.attack()
        await self.research_buildings()
        if len(self.units(NEXUS)) > 1:
            await self.research()

    async def build_workers(self):
        for nexus in self.units(NEXUS).ready.noqueue:
            if self.can_afford(PROBE) and self.units(PROBE).amount < self.units(NEXUS).amount * 20:
                await self.do(nexus.train(PROBE))

    async def build_pylons(self):
        if self.supply_left < 5 and not self.already_pending(PYLON) and self.can_afford(PYLON):
            nexuses = self.units(NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=nexuses.first)

    async def build_assimilators(self):
        for nexus in self.units(NEXUS).ready:
            vespenes = self.state.vespene_geyser.closer_than(15.0, nexus)
            for vespene in vespenes:
                if not self.can_afford(ASSIMILATOR):
                    break
                worker = self.select_build_worker(vespene.position)
                if worker is None:
                    break
                if not self.units(ASSIMILATOR).closer_than(1.0, vespene).exists:
                    await self.do(worker.build(ASSIMILATOR, vespene))

    async def expand(self):
        mineral_number = self.state.mineral_field.amount

        if (self.units(NEXUS).amount < 3 or mineral_number < 20) and self.can_afford(NEXUS):
            await self.expand_now()

    async def offensive_force_buildings(self):
        if self.units(PYLON).ready.exists:
            pylon = self.units(PYLON).ready.random
            if self.units(GATEWAY).ready.exists and not self.units(CYBERNETICSCORE):
                if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                    await self.build(CYBERNETICSCORE, near=pylon)
            elif len(self.units(GATEWAY)) < 3:
                if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                    await self.build(GATEWAY, near=pylon)
            # elif len(self.units(GATEWAY)) == 3 and len(self.units(STARGATE)) < 1:
            #     if self.can_afford(STARGATE) and not self.already_pending(STARGATE):
            #         await  self.build(STARGATE, near=pylon)

    async def build_offensive_force(self):
        for gw in self.units(GATEWAY).ready.noqueue:
            if self.can_afford(STALKER) and self.supply_left > 0:
                await self.do(gw.train(STALKER))
        for sg in self.units(STARGATE).ready.noqueue:
            if self.can_afford(VOIDRAY) and self.supply_left > 0:
                await self.do(sg.train(VOIDRAY))

    def find_target(self):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]

    async def attack(self):
        if self.units(STALKER).amount > 30:
            for s in self.units(STALKER).idle:
                await self.do(s.attack(self.find_target()))
        elif self.units(STALKER).amount > 3:
            for nexus in self.units(NEXUS).ready:
                if len(self.known_enemy_units.closer_than(30, nexus)) > 0:
                    for s in self.units(STALKER).idle:
                        await self.do(s.attack(random.choice(self.known_enemy_units.closer_than(30, nexus))))

    async def research_buildings(self):
        if self.units(PYLON).ready.exists:
            pylon = self.units(PYLON).ready.random
            if self.units(GATEWAY).ready.exists:
                if not self.units(FORGE):
                    if self.can_afford(FORGE) and not self.already_pending(FORGE):
                        await self.build(FORGE, near=pylon)
                elif self.units(FORGE).ready.exists:
                    frg = self.units(FORGE).ready.random
                    if len(await self.get_available_abilities(frg)) == 0:
                        if self.can_afford(TWILIGHTCOUNCIL) and not self.already_pending(TWILIGHTCOUNCIL):
                            await self.build(TWILIGHTCOUNCIL, near=pylon)


    async def research(self):
        # if self.units(FORGE).ready.exists:
        #     frg = self.units(FORGE).ready.random
        #     if self.can_afford(PROTOSSGROUNDWEAPONSLEVEL1):
        #         await self.do(frg(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1))
        if self.units(FORGE).ready.exists:
            for frg in self.units(FORGE).idle:
                abilities = await self.get_available_abilities(frg)
                for ability in abilities:
                    if self.can_afford(ability):
                        await self.do(frg(ability))


run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, ScapogoBot()),
    Computer(Race.Terran, Difficulty.Medium)
    ], realtime=False)
