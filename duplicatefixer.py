from __future__ import unicode_literals

import os
from app import User, Submission
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get('DATABASE_URL')

if __name__ == '__main__':
    engine = sa.create_engine(DATABASE_URL)
    session = sessionmaker(autoflush=True)
    session.configure(bind=engine)
    sess = session()

    duplicates = []
    users = User.all(sess)

    while users:
        user = users.pop()
        submissions = Submission.get_all_for_user(user, sess)
        while submissions:
            currentsub = submissions[0]
            for sub in submissions[1:]:
                print "|================|"
                print sub.id, sub.user_id, sub.question_id
                print currentsub.id, currentsub.user_id, currentsub.question_id
                if (sub.question_id, sub.user_id) == (currentsub.question_id,
                                                      currentsub.user_id):
                    duplicates.append(sub)
                    submissions.remove(sub)
                    raw_input("\n***Found***\n")
            submissions.remove(currentsub)
    raw_input(str(len(duplicates)) + " duplicates found")
    if duplicates:
        for sub in duplicates:
            print sub.id, sub.user_id, sub.question_id
            sess.delete(
                sess.query(Submission).filter(Submission.id == sub.id).one()
            )
        print "deleted"
        if raw_input("Do you want to commit? (y/n)").lower() in ["y", "yes"]:
            sess.commit()
        else:
            sess.rollback()
    print "done"
