import StateNode
import StateSpace as s
import StateSpaceFactory as ssf

def main():

    ss1 = ssf.StateSpaceFactory.load_from_file('Saves/ss1.json')
    ss2 = ssf.StateSpaceFactory.load_from_file('Saves/ss2.json')

    ss1.visualize('ss1_visualized')
    ss2.visualize('ss2_visualized')

    print(f"ss1 == ss2: {ss1 == ss2}")
    print(f"Similarity between ss1 and ss2: {ss1.similarity_score(ss2)}")

    ss3 = ssf.StateSpaceFactory.create_random(3)
    ss4 = ssf.StateSpaceFactory.create_random(3)
    ss3.save_to_file('ss3')
    ss4.save_to_file('ss4')
    ss3.visualize('ss3_visualized')
    ss4.visualize('ss4_visualized')

    print(f"Similarity between ss3 and ss4: {ss3.similarity_score(ss4)}")
if __name__ == "__main__":
    main()