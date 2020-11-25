import random
from progress_bar import ProgressBar
from P_Functions import P_constrain, P_map
import numpy as np
# ToDo: change schedule flag to -1, to account for demand id of 1


class ResourcePool:

    def __init__(self):
        self.resourceList = []
        self.demandList = []
        self.exhaustedSkills = []

        # Model paramaters
        self.NUM_INTERVALS = 60 * 12 * 60  # Hours * Minutes * Seconds
        self.MAX_INTERVAL = self.NUM_INTERVALS - 1
        self.NUM_CALLS = 20000
        self.NUM_RESOURCES = 170
        self.SHIFT_LENGTH = 8 * 60 * 60  # Hours * Minutes * Seconds
        self.MAX_DURATION = 300
        self.MAX_DELAY_BEFORE_CANCEL = 0
        self.minAvailableInterval = self.MAX_INTERVAL
        self.NUM_SKILLS = 3
        self.WRITE_TO_FILE = False

    def createResources(self):
        print('Creating employee list...')
        toolbar_width = 40
        pb = ProgressBar(toolbar_width=toolbar_width) 
        for x_ in range(self.NUM_RESOURCES):
            if x_ % round(self.NUM_RESOURCES / toolbar_width) == 0 and x_ > 0:
                # print(round(x_ * 100 / self.NUM_RESOURCES))
                pb.update(x_, self.NUM_RESOURCES)

            # start_interval = random.choices([0*60, 60*60, 120*60, 180*60, 240*60], weights=[5,10,50,10,5],k=1)[0]
            start_interval = P_constrain(np.random.normal(), -2.35, 3)
            start_interval = P_map(start_interval, -2.35, 3, 0, 4.999)
            start_interval = int(start_interval * 60 * 60)
            temp_sch = [0 for x in range(start_interval)]
            temp_sch.extend([1 for x in range(self.SHIFT_LENGTH)])
            temp_sch.extend([0 for x in range((self.NUM_INTERVALS) - (self.SHIFT_LENGTH) - (start_interval))])
            usage = [0 for x in range(self.NUM_INTERVALS)]
            skills = ['LEVEL_1', 'LEVEL_2', 'LEVEL_3']
            skill = [random.choice(skills)]
            if random.randint(0, 100) <= 30:
                skill.append(random.choice([x_ for x_ in skills if x_ not in skill]))
            self.addResource({'id': x_ + 10, 'schedule': temp_sch, 'utilization': usage, 'skills': skill})
        pb.update(1, 1)
        pb.clean()

    def createDemand(self):
        print('Creating demand list...')
        toolbar_width = 40
        pb = ProgressBar(toolbar_width=toolbar_width) 
        for x_ in range(self.NUM_CALLS):
            if x_ % round(self.NUM_CALLS / 10) == 0:
                # print(round(x_ * 100 / self.NUM_CALLS))
                pb.update(x_, self.NUM_CALLS)
            # start_interval = random.randint(0, self.MAX_INTERVAL-self.MAX_DURATION-1)
            # start_interval = int((np.random.normal(self.MAX_INTERVAL / 2,5000)))
            # start_interval = int((np.random.normal(self.MAX_INTERVAL / 2, self.MAX_INTERVAL / 4)))
            start_interval = np.random.normal()
            start_interval = P_map(start_interval, -3.0, 3.0, 0, self.MAX_INTERVAL - self.MAX_DURATION - 1)
            start_interval = int(P_constrain(start_interval, 0, self.MAX_INTERVAL - self.MAX_DURATION - 1))
            # print(start_interval)
            duration = random.randint(3, self.MAX_DURATION)
            skill = random.choice(['LEVEL_1', 'LEVEL_2', 'LEVEL_3'])
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
        for res in self.resourceList:
            for k, available in enumerate(res['schedule']):
                if available == 1:
                    if k < self.minAvailableInterval:
                        self.minAvailableInterval = k
                    break
            if self.minAvailableInterval == 0:  # If earliest interval with availability is the very first interval,
                break						   # then there is no need to check any more resources
        #print(self.minAvailableInterval)

    def findAvailableResource(self, demand):
        filtered_list = [res for res in self.resourceList if demand['skill'] in res['skills']]
        if self.MAX_DELAY_BEFORE_CANCEL > 0:
            #if demand['interval'] + self.MAX_DELAY_BEFORE_CANCEL >= self.NUM_INTERVALS:
                #MAX_INTERVAL_TO_CHECK = self.NUM_INTERVALS
            #else:
                #MAX_INTERVAL_TO_CHECK = demand['interval'] + self.MAX_DELAY_BEFORE_CANCEL
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
        #build in logic for different return codes depending on outcome
        if interval == self.NUM_INTERVALS-1:
            return 'FAIL_EXHAUSTED'
        else:
            return 'FAIL'
        

    def runSimulation(self):
        abort = False
        twidth = 40
        pb = ProgressBar(twidth)
        for k, demand in enumerate(self.demandList):
            if k % round((self.NUM_CALLS / 40)) == 0:
                #print(round(k * 100 / self.NUM_CALLS))
                pb.update(k, len(self.demandList))
            if demand['skill'] in self.exhaustedSkills:
                continue
            assigned = self.findAvailableResource(demand)
            if assigned == 'FAIL' or assigned == 'FAIL_EXHAUSTED':
                if demand['skill'] not in self.exhaustedSkills and assigned == 'FAIL_EXHAUSTED':
                    self.exhaustedSkills.append(demand['skill'])
                    #print('No employees available beginning at interval: ' + str(demand['interval']) + ' for skill: ' + demand['skill'])
                    #turned off due to max interval code interfering with this logic
                if len(self.exhaustedSkills) == self.NUM_SKILLS:
                    print(f'All skills exhausted. Simulated {k} out of {self.NUM_CALLS} demand events.')
                    abort = True #switch
                if abort == True:
                    break
        pb.update(k+1,len(self.demandList))
        pb.clean()

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
        res_utilization = round(100 * utilization / available,2)
        
        avg_delay = 0
        if missed_calls > 0:
            avg_delay = round(total_delay / missed_calls, 2)

        unanswered_perc = round(100 * unanswered_calls / total_calls, 2)
        calc_svl = round(100 - (100 * out_svl / total_calls), 2)
        delayed_perc = round(100 * missed_calls / total_calls, 2)

        print(f'Total calls: {total_calls}')
        print(f'Number of resources: {self.NUM_RESOURCES}')
        print(f'Service level ({SERVICE_LEVEL}): {calc_svl}%')
        print(f'Delayed calls: {missed_calls} ({delayed_perc}%)')
        print(f'Unanswered calls: {unanswered_calls} ({unanswered_perc}%)')
        print(f'Average delay: {avg_delay}')
        print(f'Max delay: {max_delay}')
        print(f'Resource Utilization: {res_utilization}%')

        if self.WRITE_TO_FILE == True:
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
                    #print(f"""INSERT INTO tblDemand VALUES ({w_['id']}, {w_['interval']}, {w_['duration']},'{w_['skill']}');""")
                    #crsr.execute(f"""INSERT INTO tblDemand VALUES ({w_['id']}, {w_['interval']}, {w_['duration']},'{w_['skill']}');""")
            conn.commit()

            crsr.execute("""DROP TABLE IF EXISTS tblResources;""")
            conn.commit()
            crsr.execute("""CREATE TABLE tblResources (ID BIGINT, SCHEDULE TINYINT, UTILIZATION BIGINT, SKILLS STRING);""")
            conn.commit()

        
            twidth = 40
            pb = ProgressBar(twidth)
            with open('resource_stats.csv', 'w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=['id','interval','schedule','utilization'], lineterminator="\n")
                writer.writeheader()
                for k, w_ in enumerate(self.resourceList):
                    #print(f"""INSERT INTO tblResources VALUES ({w_['id']}, '{w_['skills'][0]}');""")
                    #crsr.execute(f"""INSERT INTO tblResources VALUES ({w_['id']}, '{w_['skills'][0]}');""")
                    pb.update(k, len(self.resourceList))
                    for i_ in range(self.NUM_INTERVALS):
                        row = {'id' : w_['id'], 'interval' : str(i_), 'schedule':w_['schedule'][i_], 'utilization':w_['utilization'][i_]}
                        #crsr.execute(f"""INSERT INTO tblResources VALUES ({w_['id']}, {w_['schedule'][i_]}, {w_['utilization'][i_]}, '{w_['skills'][0]}');""")
                        writer.writerow(row)
            pb.update(1,1)
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
resourcePool.runSimulation()

print('End of simulation.')
resourcePool.printStatistics()
