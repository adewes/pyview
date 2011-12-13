from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, Text, MetaData, ForeignKey
from sqlalchemy.orm import mapper
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relation, backref

Base = declarative_base()

class DatacubeMapper(Base):

  __tablename__ = 'datacubes'


  id = Column(Integer, primary_key=True)
  name = Column(String)
  description = Column(Text)
  parent_id = Column(Integer,ForeignKey('datacubes.id'))
  
  parent = relation('DatacubeMapper',remote_side = [id])

  children = relation('DatacubeMapper', order_by='DatacubeMapper.id', remote_side=[parent_id])
  
  def __repr__(self):
    return "<%s>" % self.name
    
class DatacubeTable(Base):

  __tablename__ = 'datacubes'  
  __table_args__ = {'schema': 'events', 'autoload': True}


if __name__ == '__main__':
  
  Session = sessionmaker()
  engine = create_engine('sqlite:///datacubes2.sqlite', echo=False)

  Base.metadata.create_all(engine)
    
  Session.configure(bind=engine)
  session = Session()

  
  datacube_table = Table(metadata, "tablename", autoload=True)

#  cube = DatacubeMapper(name = "test")
#  session.add(cube)
#  session.commit()
  for cube in session.query(DatacubeMapper):
    print cube.children,cube.parent
