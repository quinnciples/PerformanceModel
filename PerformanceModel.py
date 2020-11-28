import random
from collections import defaultdict
from progress_bar import ProgressBar
from P_Functions import P_constrain, P_map
import numpy as np


class ResourcePool:

    version = '1.0'

    def __init__(self):
        self.resourceList = []
        self.demandList = []
        self.exhaustedSkills = []
        self.queue = defaultdict(list)

        # Model paramaters
        self.NUM_INTERVALS = 12 * 60 * 60  # 12 Hours
        self.MAX_INTERVAL = self.NUM_INTERVALS - 1
        self.NUM_CALLS = 15000
        self.NUM_RESOURCES = 170
        self.SHIFT_LENGTH = 8 * 60 * 60  # 8 Hours
        self.MAX_DURATION = 300
        self.MAX_DELAY_BEFORE_CANCEL = 0
        self.NUM_SKILLS = 3
        self.WRITE_TO_FILE = False

    def createResources(self):

        def determineStartingInterval():
            start_interval = P_constrain(np.random.normal(), -3.0, 3.0)
            start_interval = P_map(start_interval, -3.0, 3.0, 0, 3.999)
            start_interval = int(start_interval * 60 * 60)
            return start_interval

        def determineSchedule(start_interval):
            # Build out the employee's schedule
            # Prefill 0's from the beginning of the day until the start of this employee's shift
            temp_sch = [0 for x in range(start_interval)]
            # Fill in 1's for the duration of this employee's shift
            temp_sch.extend([1 for x in range(self.SHIFT_LENGTH)])
            # Fill in 0's from the end of this employee's shift until the end of the day
            temp_sch.extend([0 for x in range(self.NUM_INTERVALS - self.SHIFT_LENGTH - start_interval)])
            return temp_sch

        def determineSkillAssignments():
            SKILLS = ['LEVEL_1', 'LEVEL_2', 'LEVEL_3']
            skill = [random.choice(SKILLS)]
            if random.randint(0, 100) <= 30:
                skill.append(random.choice([x_ for x_ in list(set(SKILLS) - set(skill))]))
            return skill

        print('Creating employee list...')
        toolbar_width = 40
        pb = ProgressBar(toolbar_width=toolbar_width)

        for x_ in range(self.NUM_RESOURCES):
            pb.update(x_, self.NUM_RESOURCES)

            # Select the start time for this employee's shift
            start_interval = determineStartingInterval()

            # Build out the employee's schedule
            schedule = determineSchedule(start_interval)

            utilization = [0 for x in range(self.NUM_INTERVALS)]

            skillset = determineSkillAssignments()

            self.addResource({'id': x_ + 10, 'schedule': schedule, 'utilization': utilization, 'skills': skillset})
        pb.update(1, 1)
        pb.clean()

    def createDemand(self):
        def determineStartingInterval():
            start_interval = P_constrain(np.random.normal(), -3.0, 3.0)
            start_interval = P_map(start_interval, -3.0, 3.0, 15 * 60, self.MAX_INTERVAL - self.MAX_DURATION - 1)
            start_interval = int(P_constrain(start_interval, 0, self.MAX_INTERVAL - self.MAX_DURATION - 1))
            return start_interval

        def determineSkillAssignments():
            SKILLS = ['LEVEL_1', 'LEVEL_2', 'LEVEL_3']
            skill = random.choice(SKILLS)
            return skill

        def determineDuration():
            return int(P_map(P_constrain(np.random.normal(), -3.0, 3.0), -3.0, 3.0, 5, self.MAX_DURATION))

        print('Creating demand list...')
        toolbar_width = 40
        pb = ProgressBar(toolbar_width=toolbar_width)
        for x_ in range(self.NUM_CALLS):
            pb.update(x_, self.NUM_CALLS)

            start_interval = determineStartingInterval()
            duration = determineDuration()
            skill = determineSkillAssignments()

            self.addDemand({'id': x_ + 10, 'interval': start_interval, 'duration': duration, 'skill': skill})

        pb.update(1, 1)
        pb.clean()

    def addResource(self, resource):
        self.resourceList.append(resource)

    def addDemand(self, demand):
        self.demandList.append(demand)

    def sortDemand(self, sortKey):
        self.demandList.sort(key=lambda x: x[sortKey])

    def prepareSimulation(self):
        self.sortDemand('interval')
        minAvailableInterval = self.MAX_INTERVAL
        for res in self.resourceList:
            for k, available in enumerate(res['schedule']):
                if available == 1:
                    if k < minAvailableInterval:
                        minAvailableInterval = k
                    break
            if minAvailableInterval == 0:  # If earliest interval with availability is the very first interval,
                break					   # then there is no need to check any more resources

    def findAvailableResource(self, demand):
        filtered_list = [res for res in self.resourceList if demand['skill'] in res['skills']]
        if self.MAX_DELAY_BEFORE_CANCEL > 0:
            # if demand['interval'] + self.MAX_DELAY_BEFORE_CANCEL >= self.NUM_INTERVALS:
            #   MAX_INTERVAL_TO_CHECK = self.NUM_INTERVALS
            # else:
            #   MAX_INTERVAL_TO_CHECK = demand['interval'] + self.MAX_DELAY_BEFORE_CANCEL
            MAX_INTERVAL_TO_CHECK = P_constrain(int(demand['interval']) + self.MAX_DELAY_BEFORE_CANCEL, int(demand['interval']) + self.MAX_DELAY_BEFORE_CANCEL, self.NUM_INTERVALS)
        else:
            MAX_INTERVAL_TO_CHECK = self.NUM_INTERVALS
        for interval in range(demand['interval'], MAX_INTERVAL_TO_CHECK):
            for res in filtered_list:
                if res['schedule'][interval] == 1 and res['utilization'][interval] == 0 and demand['skill'] in res['skills']:
                    demand['assigned_resource'] = res['id']
                    demand['answered_interval'] = interval
                    for i in range(interval, interval + demand['duration']):
                        if i <= self.MAX_INTERVAL:  # needed to make sure utilization doesn't exceed the model's time intervals
                            res['utilization'][i] = demand['id']
                    return 'SUCCESS'
        # Build in logic for different return codes depending on outcome
        if interval == self.NUM_INTERVALS - 1:
            return 'FAIL_EXHAUSTED'
        else:
            return 'FAIL'

    def runSimulation(self):
        toolbar_width = 40
        pb = ProgressBar(toolbar_width=toolbar_width)
        for k, demand in enumerate(self.demandList):
            if k % round((self.NUM_CALLS / 40)) == 0:
                # print(round(k * 100 / self.NUM_CALLS))
                pb.update(k, self.NUM_CALLS)
            if demand['skill'] in self.exhaustedSkills:
                continue
            assigned = self.findAvailableResource(demand)
            if assigned == 'FAIL' or assigned == 'FAIL_EXHAUSTED':
                if demand['skill'] not in self.exhaustedSkills and assigned == 'FAIL_EXHAUSTED':
                    self.exhaustedSkills.append(demand['skill'])
                    # print('No employees available beginning at interval: ' + str(demand['interval']) + ' for skill: ' + demand['skill'])
                    # turned off due to max interval code interfering with this logic
                if len(self.exhaustedSkills) == self.NUM_SKILLS:
                    pb.update(1, 1)
                    print(f'\nAll skills exhausted. Simulated {k} out of {self.NUM_CALLS} demand events.')
                    pb.update(1, 1)
                    break
        pb.update(k + 1, len(self.demandList))
        pb.clean()

    def runAdvancedSimulation(self):
        for tick in range(self.NUM_INTERVALS):
            # Loop through demand items in the current queue
            for demand in self.queue[tick]:
                # Try to assign these items to an available resource
                pass

            # Loop through items in the demand simulation.
            for demand in self.demandList:
                # Assign this to an available resource if possible. If not, add them to the queue.
                pass

    def printStatistics(self):
        SERVICE_LEVEL = 20
        total_calls = len(self.demandList)
        missed_calls = 0
        delay = 0
        total_delay = 0
        max_delay = 0
        out_svl = 0
        unanswered_calls = 0
        print('Calculating demand statistics...')
        for call in self.demandList:
            if 'answered_interval' not in call:
                unanswered_calls += 1
                missed_calls += 1
                out_svl += 1
            else:
                if call['interval'] != call['answered_interval']:
                    missed_calls += 1
                    delay = call['answered_interval'] - call['interval']
                    total_delay += delay
                    if delay > max_delay:
                        max_delay = delay
                    if delay > SERVICE_LEVEL:
                        out_svl += 1

        print('Calculating resource statistics...')
        utilization = 0
        available = 0
        for res in self.resourceList:
            available += self.SHIFT_LENGTH
            for moment in res['utilization']:
                if moment > 1:
                    utilization += 1
        res_utilization = round(100 * utilization / available, 2)

        if missed_calls > 0:
            avg_delay = round(total_delay / missed_calls, 2)
            asa = round(total_delay / total_calls, 0)
        else:
            avg_delay = 0
            asa = 0

        unanswered_perc = round(100 * unanswered_calls / total_calls, 2)
        calc_svl = round(100 - (100 * out_svl / total_calls), 2)
        delayed_perc = round(100 * missed_calls / total_calls, 2)

        print(f'Total calls: {total_calls}')
        print(f'Number of resources: {self.NUM_RESOURCES}')
        print(f'Service level ({SERVICE_LEVEL}): {calc_svl}%')
        print(f'Delayed calls: {missed_calls} ({delayed_perc}%)')
        print(f'Unanswered calls: {unanswered_calls} ({unanswered_perc}%)')
        print(f'Average seconds to answer: {asa:.0f}')
        print(f'Average delay: {avg_delay}')
        print(f'Max delay: {max_delay}')
        print(f'Resource Utilization: {res_utilization}%')

        if self.WRITE_TO_FILE:
            import sqlite3
            import csv
            conn = sqlite3.connect('perfmodel.db')
            crsr = conn.cursor()
            crsr.execute("""DROP TABLE IF EXISTS tblDemand;""")
            conn.commit()
            crsr.execute("""CREATE TABLE tblDemand (ID BIGINT PRIMARY KEY, INTERVAL BIGINT, DURATION BIGINT, SKILL STRING);""")
            conn.commit()

            print('Writing to file...')
            with open('demand_stats.csv', 'w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=self.demandList[0].keys(), lineterminator="\n")
                writer.writeheader()
                for w_ in self.demandList:
                    writer.writerow(w_)
                    # print(f"""INSERT INTO tblDemand VALUES ({w_['id']}, {w_['interval']}, {w_['duration']},'{w_['skill']}');""")
                    # crsr.execute(f"""INSERT INTO tblDemand VALUES ({w_['id']}, {w_['interval']}, {w_['duration']},'{w_['skill']}');""")
            conn.commit()

            crsr.execute("""DROP TABLE IF EXISTS tblResources;""")
            conn.commit()
            crsr.execute("""CREATE TABLE tblResources (ID BIGINT, SCHEDULE TINYINT, UTILIZATION BIGINT, SKILLS STRING);""")
            conn.commit()

            toolbar_width = 40
            pb = ProgressBar(toolbar_width=toolbar_width)
            with open('resource_stats.csv', 'w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=['id', 'interval', 'schedule', 'utilization'], lineterminator="\n")
                writer.writeheader()
                for k, w_ in enumerate(self.resourceList):
                    # print(f"""INSERT INTO tblResources VALUES ({w_['id']}, '{w_['skills'][0]}');""")
                    # crsr.execute(f"""INSERT INTO tblResources VALUES ({w_['id']}, '{w_['skills'][0]}');""")
                    pb.update(k, len(self.resourceList))
                    for i_ in range(self.NUM_INTERVALS):
                        row = {'id': w_['id'], 'interval': str(i_), 'schedule': w_['schedule'][i_], 'utilization': w_['utilization'][i_]}
                        # crsr.execute(f"""INSERT INTO tblResources VALUES ({w_['id']}, {w_['schedule'][i_]}, {w_['utilization'][i_]}, '{w_['skills'][0]}');""")
                        writer.writerow(row)
            pb.update(1, 1)
            pb.clean()
            conn.commit()
            conn.close()


resourcePool = ResourcePool()

resourcePool.createResources()

# Create demand input
resourcePool.createDemand()

print('Sorting demand list...')
print('Optimizing simulation paramaters')
resourcePool.prepareSimulation()

print('Running simulation...')
# resourcePool.runSimulation()
resourcePool.runAdvancedSimulation()

print('End of simulation.')
# resourcePool.printStatistics()
