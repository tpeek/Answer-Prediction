from __future__ import unicode_literals

import os
import sys
from app import Question
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://wesleywooten@localhost:5432/AP_test'
    #'postgresql://power_user:hownowbrownsnake@localhost:5432/test1'
    #'postgresql://power_user:nopassword@localhost:5432/test1'
)
HELP = """
     new / n:    create new question

  delete / d:    delete an existing question

    show / s:    print out list of existing questions

  commit / c:    commit changes

rollback / r:    rollback changes

    file / f:    parse questions from file
                   file should contain questions seperated by new lines only

    exit / e:    exit
"""


if __name__ == '__main__':
    engine = sa.create_engine(DATABASE_URL)
    session = sessionmaker(autoflush=True)
    session.configure(bind=engine)
    sess = session()
    if sys.argv[-1] != "add_question.py" and os.path.isfile(sys.argv[-1]):
        with open(sys.argv[-1]) as questions:
            for q in questions.read().split("\n"):
                q = unicode(q)
                if not sess.query(Question).filter(Question.text == q).one():
                    Question.new(q, sess)
                    print "Added ", q
                else:
                    print "Already in DB:", q
        if raw_input("Are you sure you want to commit? (Y/N)\n>"
                     ).lower() in ['y', 'yes']:
            sess.commit()
            print "Commited"
        else:
            sess.rollback()
            print "Did not commit"
    else:
        for q in Question.all(sess):
                print q.id, ":", q.text
        while True:
            inp = raw_input("Enter Command:\n>").lower()
            if inp in ["new", "n"]:
                    q = unicode(raw_input("Enter Question Text:\n>"))
                    if not sess.query(Question).filter(
                            Question.text == q).one():
                        Question.new(q, sess)
                    else:
                        print "Question Must Be Unique"
            elif inp in ["delete", "d"]:
                for q in Question.all(sess):
                    print q.id, ":", q.text
                i = int(raw_input("Select Question (by id):\n>"))
                sess.delete(
                    sess.query(Question).filter(Question.id == i).first()
                )
            elif inp in ["show", "s"]:
                for q in Question.all(sess):
                    print q.id, ":", q.text
            elif inp in ["commit", "c"]:
                if raw_input("Are you sure you want to commit? (Y/N):"
                             ).lower() in ["y", "yes"]:
                    sess.commit()
            elif inp in ["rollback", "r"]:
                print "Rolling back"
                sess.rollback()
            elif inp in ["file", "f"]:
                filename = raw_input("Enter path:\n>")
                with open(filename) as file:
                    questions = file.read().split("\n")
                    for q in questions:
                        Question.new(q, sess)
            elif inp in ["help", "h"]:
                print HELP
            elif inp in ["exit", "e"]:
                break
            else:
                print "Not a valid command. enter help for list of commands"
